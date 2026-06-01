"""
Classifier
==========
Provides classify_text(text) → (category, urgency, sentiment)

Strategy (tried in order, first success wins):
  1. NLI zero-shot  — cross-encoder/nli-deberta-v3-small loaded from
                      src/nlp/nli_classifier.py. Requires `transformers`
                      and `torch` to be installed. Downloads the model
                      (~180 MB) on first use and caches it locally.
  2. TF-IDF models  — pre-trained Logistic Regression + TF-IDF pipelines
                      from src/models/ (trained via classification/train.py).
  3. Keyword rules  — deterministic keyword-matching heuristic that always
                      works with no dependencies.

Sentiment is always computed by the rule-based lexicon (Strategy 3 level)
regardless of which strategy handles category/urgency — it is fast, requires
no model, and is accurate enough for civic complaint text.
"""

import os
import joblib

# ---------------------------------------------------------------------------
# Strategy 2: TF-IDF pkl models (loaded once at import time)
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")

CATEGORY_MODEL_PATH = os.path.join(MODELS_DIR, "category_classifier.pkl")
URGENCY_MODEL_PATH = os.path.join(MODELS_DIR, "urgency_classifier.pkl")

_category_model = None
_urgency_model = None


def _load_tfidf_models() -> None:
    """Load pre-trained TF-IDF + Logistic Regression pkl models if present."""
    global _category_model, _urgency_model
    if os.path.exists(CATEGORY_MODEL_PATH) and os.path.exists(URGENCY_MODEL_PATH):
        try:
            _category_model = joblib.load(CATEGORY_MODEL_PATH)
            _urgency_model = joblib.load(URGENCY_MODEL_PATH)
            print("[Classifier] Loaded TF-IDF/Logistic Regression models (Strategy 2).")
        except Exception as exc:
            print(f"[Classifier] Failed to load TF-IDF models: {exc}. Strategy 2 disabled.")
            _category_model = None
            _urgency_model = None
    else:
        print("[Classifier] TF-IDF model files not found (Strategy 2 disabled).")
        print("  -> Run: cd src && python classification/train.py")


_load_tfidf_models()


# ---------------------------------------------------------------------------
# Strategy 3: Sentiment analysis — rule-based lexicon (always used)
# ---------------------------------------------------------------------------

_NEGATIVE_WORDS = {
    "awful", "bad", "terrible", "chaotic", "dangerous", "damaged", "broken",
    "dirty", "horrible", "worst", "pathetic", "disgusting", "hazard",
    "accident", "collapsed", "flooded", "overflowing", "toxic", "sick",
    "suffering", "emergency", "fire", "exploded", "fallen", "blocked",
    "unhygienic", "unsafe", "injured", "dead", "attack",
}

_POSITIVE_WORDS = {
    "good", "great", "thanks", "resolved", "fixed", "improved",
    "clean", "working", "repaired", "restored", "better",
}

def _analyze_sentiment(text: str) -> str:
    """Simple lexicon-based sentiment: POSITIVE / NEGATIVE / NEUTRAL."""
    words = set(text.lower().split())
    neg_hits = len(words & _NEGATIVE_WORDS)
    pos_hits = len(words & _POSITIVE_WORDS)
    if neg_hits > pos_hits:
        return "NEGATIVE"
    if pos_hits > neg_hits:
        return "POSITIVE"
    return "NEUTRAL"


# ---------------------------------------------------------------------------
# Strategy 3: Keyword fallback — deterministic, no dependencies
# ---------------------------------------------------------------------------

_CATEGORY_KEYWORDS = {
    "Roads & Traffic": ["pothole", "road", "traffic", "street", "accident", "highway", "divider", "footpath"],
    "Water & Sanitation": ["water", "pipe", "leak", "drain", "flood", "sewage", "tap", "supply", "brown"],
    "Electricity": ["power", "electricity", "outage", "light", "wire", "transformer", "voltage", "current"],
    "Garbage & Waste": ["garbage", "waste", "trash", "dustbin", "litter", "dump", "collection"],
    "Flooding": ["flood", "waterlog", "waterlogging", "submerged", "inundated", "stagnant", "puddle"],
    "Public Infrastructure": ["park", "bench", "toilet", "bridge", "building", "shelter", "playground"],
    "Noise & Pollution": ["noise", "pollution", "smoke", "dust", "chemical", "smell", "loud", "factory"],
}

_URGENCY_KEYWORDS = {
    "HIGH": ["immediate", "danger", "accident", "emergency", "fire", "collapsed", "exploded",
             "fallen", "attack", "toxic", "dead", "injured", "submerged", "chaotic", "awful"],
    "MEDIUM": ["fix", "broken", "outage", "bother", "blinking", "delayed", "overflowing",
               "blocked", "damaged", "not working", "unhygienic"],
}

def _keyword_classify(text: str) -> tuple[str, str]:
    """Keyword-based fallback for category and urgency."""
    text_lower = text.lower()

    # Category
    best_category = "General"
    best_score = 0
    for category, keywords in _CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > best_score:
            best_score = score
            best_category = category

    # Urgency
    urgency = "LOW"
    for level in ["HIGH", "MEDIUM"]:
        if any(kw in text_lower for kw in _URGENCY_KEYWORDS[level]):
            urgency = level
            break

    return best_category, urgency


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_text(text: str) -> tuple[str, str, str]:
    """
    Classify complaint text into category, urgency, and sentiment.

    Args:
        text: Cleaned/preprocessed complaint text.

    Returns:
        (category, urgency, sentiment)
        e.g. ("Roads & Traffic", "HIGH", "NEGATIVE")

    Strategy order:
        1. NLI zero-shot  (cross-encoder/nli-deberta-v3-small)
        2. TF-IDF models  (pre-trained Logistic Regression pkl)
        3. Keyword rules  (always available, no dependencies)
    """
    if not text:
        return "General", "LOW", "NEUTRAL"

    # Sentiment is always rule-based — fast and dependency-free
    sentiment = _analyze_sentiment(text)

    # ------------------------------------------------------------------
    # Strategy 1: NLI zero-shot classifier (primary)
    # ------------------------------------------------------------------
    try:
        from nlp.nli_classifier import classify_category, classify_urgency, is_available  # noqa: PLC0415
        if is_available():
            category, _ = classify_category(text)
            urgency, _  = classify_urgency(text)
            return category, urgency, sentiment
    except Exception as exc:
        print(f"[Classifier] NLI strategy failed: {exc}. Trying TF-IDF models.")

    # ------------------------------------------------------------------
    # Strategy 2: pre-trained TF-IDF + Logistic Regression pkl models
    # ------------------------------------------------------------------
    if _category_model is not None and _urgency_model is not None:
        try:
            category = _category_model.predict([text])[0]
            urgency  = _urgency_model.predict([text])[0]
            return category, urgency, sentiment
        except Exception as exc:
            print(f"[Classifier] TF-IDF strategy failed: {exc}. Falling back to keywords.")

    # ------------------------------------------------------------------
    # Strategy 3: keyword-matching heuristic (always available)
    # ------------------------------------------------------------------
    category, urgency = _keyword_classify(text)
    return category, urgency, sentiment

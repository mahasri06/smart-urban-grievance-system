"""
Classifier
==========
Provides classify_text(text) → (category, urgency, sentiment)

Strategy:
  - At startup, tries to load pre-trained Naive Bayes + TF-IDF pipelines
    from src/models/. If the model files exist, they are used for all
    predictions (real ML).
  - If models are not found (e.g., train.py hasn't been run yet), falls
    back to a keyword-matching heuristic so the API still works.

To train the real models:
    cd src
    python classification/train.py
"""

import os
import joblib

# ---------------------------------------------------------------------------
# Model loading (done once at import time)
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")

CATEGORY_MODEL_PATH = os.path.join(MODELS_DIR, "category_classifier.pkl")
URGENCY_MODEL_PATH = os.path.join(MODELS_DIR, "urgency_classifier.pkl")

_category_model = None
_urgency_model = None

def _load_models():
    global _category_model, _urgency_model
    if os.path.exists(CATEGORY_MODEL_PATH) and os.path.exists(URGENCY_MODEL_PATH):
        try:
            _category_model = joblib.load(CATEGORY_MODEL_PATH)
            _urgency_model = joblib.load(URGENCY_MODEL_PATH)
            print("[Classifier] Loaded trained Naive Bayes models.")
        except Exception as e:
            print(f"[Classifier] Failed to load models: {e}. Using keyword fallback.")
            _category_model = None
            _urgency_model = None
    else:
        print("[Classifier] Model files not found. Using keyword fallback.")
        print("  → Run: cd src && python classification/train.py")

_load_models()


# ---------------------------------------------------------------------------
# Sentiment analysis (rule-based VADER-style word lists)
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
# Keyword fallback classifier
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
    Main classification function.

    Args:
        text: cleaned/preprocessed complaint text

    Returns:
        (category, urgency, sentiment)
        e.g. ("Roads & Traffic", "HIGH", "NEGATIVE")
    """
    if not text:
        return "General", "LOW", "NEUTRAL"

    # Sentiment is always rule-based (fast, no model needed)
    sentiment = _analyze_sentiment(text)

    # Category + Urgency: use trained models if available, else keyword fallback
    if _category_model is not None and _urgency_model is not None:
        try:
            category = _category_model.predict([text])[0]
            urgency = _urgency_model.predict([text])[0]
        except Exception as e:
            print(f"[Classifier] Prediction error: {e}. Falling back to keywords.")
            category, urgency = _keyword_classify(text)
    else:
        category, urgency = _keyword_classify(text)

    return category, urgency, sentiment

"""
NLI-based Zero-Shot Classifier
================================
Uses cross-encoder/nli-deberta-v3-small for zero-shot text classification.
No training data required — labels are matched via Natural Language Inference.

The model scores each candidate hypothesis against the input text using an
entailment score. Descriptive hypothesis strings are used instead of bare
label names because they give the NLI model more signal to work with.

Model:   cross-encoder/nli-deberta-v3-small (~180MB)
Requires: pip install transformers torch

The pipeline is loaded lazily on first use so API startup time is unaffected
if the model has not been downloaded yet. If loading fails for any reason,
is_available() returns False and the caller falls back gracefully.
"""

from __future__ import annotations

from typing import Optional

# ---------------------------------------------------------------------------
# Module-level state — loaded once, reused for every call
# ---------------------------------------------------------------------------

_pipeline = None
_model_loaded: Optional[bool] = None  # None = not yet attempted

MODEL_NAME = "cross-encoder/nli-deberta-v3-small"

# ---------------------------------------------------------------------------
# Label definitions
#
# Descriptive hypothesis strings outperform bare label names on NLI models.
# The model checks: does this text entail <hypothesis>?
# Richer descriptions reduce ambiguity between overlapping categories
# (e.g. "flooding" vs "water & sanitation").
# ---------------------------------------------------------------------------

CATEGORY_LABELS: dict[str, str] = {
    "Roads & Traffic":       "complaint about road damage, pothole, traffic jam, or street obstruction",
    "Water & Sanitation":    "complaint about water supply, pipe leak, sewage overflow, or sanitation",
    "Electricity":           "complaint about power outage, voltage fluctuation, sparking wire, or streetlight",
    "Flooding":              "complaint about flooding, waterlogging, or stagnant water after rain",
    "Garbage & Waste":       "complaint about garbage collection, trash overflow, or illegal dumping",
    "Noise & Pollution":     "complaint about noise, air pollution, smoke, or chemical smell",
    "Public Infrastructure": "complaint about broken park equipment, bridge, public toilet, or shelter",
}

URGENCY_LABELS: dict[str, str] = {
    "HIGH":   "this is an urgent emergency requiring immediate attention, involving danger or injury",
    "MEDIUM": "this issue is moderately serious and needs attention soon but is not an emergency",
    "LOW":    "this is a minor inconvenience or low-priority complaint",
}

# Reverse maps: hypothesis string → label name (built once at module load)
_HYPOTHESIS_TO_CATEGORY: dict[str, str] = {v: k for k, v in CATEGORY_LABELS.items()}
_HYPOTHESIS_TO_URGENCY: dict[str, str] = {v: k for k, v in URGENCY_LABELS.items()}


# ---------------------------------------------------------------------------
# Lazy loader
# ---------------------------------------------------------------------------

def _load_pipeline() -> bool:
    """
    Attempt to load the HuggingFace zero-shot-classification pipeline.
    Idempotent — subsequent calls return the cached result immediately.

    Returns:
        True  if the model loaded successfully.
        False if loading failed (missing deps, no internet, etc.).
    """
    global _pipeline, _model_loaded

    if _model_loaded is not None:
        return _model_loaded

    try:
        from transformers import pipeline as hf_pipeline  # noqa: PLC0415

        _pipeline = hf_pipeline(
            "zero-shot-classification",
            model=MODEL_NAME,
            device=-1,  # CPU only — no GPU required
        )
        _model_loaded = True
        print(f"[NLIClassifier] Loaded '{MODEL_NAME}' successfully.")

    except Exception as exc:  # broad catch — covers ImportError, OSError, etc.
        _model_loaded = False
        print(f"[NLIClassifier] Could not load NLI model: {exc}")
        print("  -> Caller should fall back to TF-IDF / keyword classifier.")

    return _model_loaded


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def is_available() -> bool:
    """
    Returns True if the NLI model is loaded and ready for inference.
    Triggers a load attempt on first call.
    """
    return _load_pipeline()


def classify_category(text: str) -> tuple[str, float]:
    """
    Classify complaint text into one of the system categories.

    Args:
        text: Raw or preprocessed complaint text.

    Returns:
        (category_label, confidence_score)
        e.g. ("Roads & Traffic", 0.87)

    Raises:
        RuntimeError: If the NLI model is not available.
    """
    if not _load_pipeline():
        raise RuntimeError("NLI model not available — call is_available() before classify_category()")

    result = _pipeline(
        text,
        candidate_labels=list(CATEGORY_LABELS.values()),
        hypothesis_template="{}",
        multi_label=False,
    )

    top_hypothesis: str = result["labels"][0]
    top_score: float = result["scores"][0]
    label = _HYPOTHESIS_TO_CATEGORY[top_hypothesis]

    return label, top_score


def classify_urgency(text: str) -> tuple[str, float]:
    """
    Classify complaint text into an urgency level.

    Args:
        text: Raw or preprocessed complaint text.

    Returns:
        (urgency_label, confidence_score)
        e.g. ("HIGH", 0.91)

    Raises:
        RuntimeError: If the NLI model is not available.
    """
    if not _load_pipeline():
        raise RuntimeError("NLI model not available — call is_available() before classify_urgency()")

    result = _pipeline(
        text,
        candidate_labels=list(URGENCY_LABELS.values()),
        hypothesis_template="{}",
        multi_label=False,
    )

    top_hypothesis: str = result["labels"][0]
    top_score: float = result["scores"][0]
    label = _HYPOTHESIS_TO_URGENCY[top_hypothesis]

    return label, top_score

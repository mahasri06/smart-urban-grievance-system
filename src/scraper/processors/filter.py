import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlp.text_preprocessor import normalize_for_keyword_matching

# Load hard-coded stemmed keywords (simple lookup)
_CONF_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config_stemmed.json"))
try:
    with open(_CONF_PATH, "r", encoding="utf-8") as _f:
        _RAW_STEMMED = json.load(_f)
except Exception:
    _RAW_STEMMED = {}


# Build normalized (stemmed/tokenized) index from the config file
_STEMMED_KEYWORD_INDEX = {}
for category, keywords in _RAW_STEMMED.items():
    processed = []
    for kw in keywords:
        tokens = normalize_for_keyword_matching(kw)
        if tokens:
            processed.append(" ".join(tokens))
    _STEMMED_KEYWORD_INDEX[category] = processed


def is_relevant(text):
    """Check relevance by stemming the incoming text and matching against
    the precomputed stemmed keywords loaded from config_stemmed.json."""
    token_text = " ".join(normalize_for_keyword_matching(text))
    for stemmed_list in _STEMMED_KEYWORD_INDEX.values():
        for stem_kw in stemmed_list:
            if stem_kw and stem_kw in token_text:
                return True
    return False


def detect_categories(text):
    matched = set()
    token_text = " ".join(normalize_for_keyword_matching(text))
    for category, stemmed_list in _STEMMED_KEYWORD_INDEX.items():
        for stem_kw in stemmed_list:
            if stem_kw and stem_kw in token_text:
                matched.add(category)
                break
    return list(matched)

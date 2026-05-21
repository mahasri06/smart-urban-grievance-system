import re
from config import CATEGORIES

ALL_TERMS = [re.escape(term) for incidents in CATEGORIES.values() for term in incidents]
RELEVANT_REGEX = re.compile("|".join(ALL_TERMS), re.IGNORECASE) if ALL_TERMS else None
CATEGORY_PATTERNS = {
    category: re.compile("|".join([re.escape(t) for t in terms]), re.IGNORECASE)
    for category, terms in CATEGORIES.items() if terms
}

def is_relevant(text):
    if not RELEVANT_REGEX:
        return False
    return bool(RELEVANT_REGEX.search(text))


def detect_categories(text):
    return [
        category for category, pattern in CATEGORY_PATTERNS.items() 
        if pattern.search(text)
    ]

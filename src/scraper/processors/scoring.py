import re
from config import COMPLAINT_TERMS, QUESTION_TERMS, INTENT_LEVELS

COMPLAINT_REGEX = re.compile("|".join([re.escape(t) for t in COMPLAINT_TERMS]), re.IGNORECASE) if COMPLAINT_TERMS else None
QUESTION_REGEX = re.compile("|".join([re.escape(t) for t in QUESTION_TERMS]), re.IGNORECASE) if QUESTION_TERMS else None
INTENT_PATTERNS = {
    level: re.compile("|".join([re.escape(t) for t in terms]), re.IGNORECASE)
    for level, terms in INTENT_LEVELS.items() if terms
}

def questioning_penalty(text):
    if not QUESTION_REGEX:
        return 0
    return len(QUESTION_REGEX.findall(text))


def complaint_score(text):
    if not COMPLAINT_REGEX:
        return 0
    return len(COMPLAINT_REGEX.findall(text))


def calculate_severity(text, categories):
    score = 0

    score += complaint_score(text) * 2
    score -= questioning_penalty(text)

    level_boosts = {
        "LEVEL_1": 1,
        "LEVEL_2": 3,
        "LEVEL_3": 5
    }

    intent_boost = 0
    for level, pattern in INTENT_PATTERNS.items():
        if pattern.search(text):
            intent_boost = max(intent_boost, level_boosts[level])

    score += intent_boost

    category_boosts = {
        "EMERGENCY": 5,
        "PUBLIC_HEALTH": 4,
        "SANITATION": 3,
        "UTILITIES": 3,
        "TRANSPORT": 2,
        "INFRASTRUCTURE": 2
    }

    for category in categories:
        score += category_boosts.get(category, 0)

    return round(score, 2)
from config import (
    COMPLAINT_TERMS,
    QUESTION_TERMS,
    INTENT_LEVELS
)


def questioning_penalty(text):
    score = 0
    for word in QUESTION_TERMS:
        if word in text:
            score += 1
    return score


def complaint_score(text):
    score = 0
    for word in COMPLAINT_TERMS:
        if word in text:
            score += 1
    return score


def calculate_severity(text, categories):

    score = 0

    # Complaint signal
    score += complaint_score(text) * 2

    # questioning penalty
    score -= questioning_penalty(text)

    # Intent boosts
    level_boosts = {

        "LEVEL_1": 1,
        "LEVEL_2": 3,
        "LEVEL_3": 5
    }

    intent_boost = 0

    for level, terms in INTENT_LEVELS.items():
        for term in terms:
            if term in text:
                intent_boost = max(
                    intent_boost,
                    level_boosts[level]
                )

    score += intent_boost

    # Category boosts
    category_boosts = {
        "EMERGENCY": 5,
        "PUBLIC_HEALTH": 4,
        "SANITATION": 3,
        "UTILITIES": 3,
        "TRANSPORT": 2,
        "INFRASTRUCTURE": 2
    }

    for category in categories:
        score += category_boosts.get(
            category,
            0
        )

    return round(score, 2)
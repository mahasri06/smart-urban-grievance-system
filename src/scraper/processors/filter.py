from config import CATEGORIES


def is_relevant(text):

    for incidents in CATEGORIES.values():
        for incident in incidents:
            if incident in text:
                return True
    return False


def detect_categories(text):
    matched = set()

    for category, incidents in CATEGORIES.items():
        for incident in incidents:
            if incident in text:
                matched.add(category)

    return list(matched)

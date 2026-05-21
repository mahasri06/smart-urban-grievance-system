import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.config import CATEGORIES


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

"""Generate a stemmed keyword JSON file from scraper.config.CATEGORIES.

Run with the project venv Python to produce src/scraper/config_stemmed.json
"""
import json
import os
from scraper.config import CATEGORIES
from nlp.text_preprocessor import normalize_for_keyword_matching

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(BASE, "scraper", "config_stemmed.json")


def build_stemmed_index(categories):
    return {
        cat: [" ".join(normalize_for_keyword_matching(inc)) for inc in incs]
        for cat, incs in categories.items()
    }


def main():
    stemmed = build_stemmed_index(CATEGORIES)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(stemmed, f, indent=2, ensure_ascii=False)
    print(f"Wrote stemmed config to: {OUT_PATH}")


if __name__ == "__main__":
    main()

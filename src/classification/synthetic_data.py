import os
import random
from typing import Iterable

import pandas as pd

from classification.data_utils import normalize_text

TEMPLATES = {
    "Noise & Pollution": [
        ("My neighbors have been blasting loud music all night and I cannot sleep.", "LOW"),
        ("There is constant construction noise coming from the site next door at 3 AM.", "MEDIUM"),
        ("Someone is running a noisy generator outside my window, it is unbearable.", "LOW"),
        ("The factory down the road is emitting thick black smoke and smells like chemicals.", "HIGH"),
        ("A group of people are partying in the street and yelling very loudly.", "LOW"),
        ("Air quality is terrible today, smog everywhere and it is hard to breathe.", "HIGH"),
        ("Car alarms have been going off for 3 hours straight on my block.", "LOW"),
    ],
    "Roads & Traffic": [
        ("There is a massive pothole on Main Street that just ruined my tire.", "MEDIUM"),
        ("Traffic is completely gridlocked at the intersection because the lights are out.", "HIGH"),
        ("A delivery truck is double parked and blocking the entire lane.", "LOW"),
        ("The street signs are completely faded and causing accidents.", "MEDIUM"),
        ("Someone left a broken down car in the middle of the road.", "MEDIUM"),
        ("There is a severe traffic jam stretching for miles due to an accident.", "HIGH"),
        ("A commercial van is parked overnight in a residential zone.", "LOW"),
        ("The sidewalk is completely blocked by construction debris.", "LOW"),
    ],
    "Water & Sanitation": [
        ("Dirty water is coming out of the tap and it smells bad.", "MEDIUM"),
        ("There is no water supply in our area since morning.", "HIGH"),
        ("Sewage is overflowing from the drain near our house.", "HIGH"),
        ("The water pipe has a leak and the street is flooded.", "HIGH"),
        ("The public toilet is blocked and unusable.", "MEDIUM"),
        ("Tap water pressure is extremely low for days.", "LOW"),
    ],
    "Electricity": [
        ("Power outage for 6 hours in our street.", "HIGH"),
        ("Voltage keeps fluctuating and appliances are at risk.", "MEDIUM"),
        ("Sparking wires are hanging near the transformer.", "HIGH"),
        ("Street light is not working at night.", "MEDIUM"),
        ("Frequent power cuts every evening.", "LOW"),
    ],
    "Garbage & Waste": [
        ("Garbage has not been collected for a week.", "MEDIUM"),
        ("Trash is overflowing from the bin and attracts dogs.", "MEDIUM"),
        ("Illegal dumping in the empty plot nearby.", "LOW"),
        ("Waste collection truck skipped our lane again.", "LOW"),
        ("Rotting waste smell is unbearable and causing illness.", "HIGH"),
    ],
    "Flooding": [
        ("The underpass is fully flooded and vehicles are stuck.", "HIGH"),
        ("Waterlogging on the main road after light rain.", "MEDIUM"),
        ("Stagnant water has been sitting for days near the market.", "MEDIUM"),
        ("Homes are getting flooded due to clogged drains.", "HIGH"),
        ("Rainwater has submerged the footpath.", "LOW"),
    ],
    "Public Infrastructure": [
        ("The public park equipment is broken and dangerous for children.", "MEDIUM"),
        ("The bus shelter glass was shattered and there is glass everywhere.", "MEDIUM"),
        ("The pedestrian bridge has loose tiles and feels unsafe.", "HIGH"),
        ("Streetlights are all broken and it feels very unsafe at night.", "MEDIUM"),
        ("The footpath is damaged and inaccessible for wheelchairs.", "LOW"),
    ],
}

COMPLEX_TEMPLATES = {
    "Noise & Pollution": [
        ("The traffic from the new park construction is so loud I can't think. It's a disaster.", "MEDIUM"),
        ("Great job fixing the road, now the trucks rattle my house and make an ungodly racket.", "MEDIUM"),
        ("There is literal garbage burning in the alley, it smells toxic.", "HIGH"),
        ("Smog from the highway is completely unbarable today. Very bad.", "HIGH"),
        ("i cnt sleep bcoz of the water pump noise from the broken pipes!!", "MEDIUM"),
    ],
    "Roads & Traffic": [
        ("The park entrance is completely blocked by a collapsed wall, forcing cars into the wrong lane.", "HIGH"),
        ("So much noise from the cars stuck in the pothole. Please fix.", "LOW"),
        ("The heavy rain completely flooded the intersection and now no one can move.", "HIGH"),
        ("ther is a huge bump on th road dat just borke my car", "MEDIUM"),
        ("Amazing infrastructure you have here, it took me 3 hours to move 2 miles.", "LOW"),
    ],
    "Water & Sanitation": [
        ("Sewage smell near the school is making kids sick.", "HIGH"),
        ("No water for 2 days, only a trickle in the morning.", "HIGH"),
        ("The drain is clogged and now the street is flooded with dirty water.", "HIGH"),
        ("tap water looks brown and tastes odd", "MEDIUM"),
    ],
    "Electricity": [
        ("Transformer keeps blowing and we hear loud bangs at night.", "HIGH"),
        ("Power cuts every hour and the freezer is ruined.", "MEDIUM"),
        ("street light flickers like a strobe, feels unsafe", "MEDIUM"),
    ],
    "Garbage & Waste": [
        ("Trash piles are blocking the lane, trucks ignore this area.", "MEDIUM"),
        ("Someone dumped construction debris next to the bus stop.", "LOW"),
        ("Rotting waste is spreading insects everywhere.", "HIGH"),
    ],
    "Flooding": [
        ("The basement is flooded again, drains can't handle rain.", "HIGH"),
        ("Waterlogging after a small shower shows drains are broken.", "MEDIUM"),
        ("The market road looks like a lake, no vehicles can pass.", "HIGH"),
    ],
    "Public Infrastructure": [
        ("The playground swing snapped and injured a child.", "HIGH"),
        ("The footbridge is rusted and shaking when people walk.", "HIGH"),
        ("Park benches are broken and unsafe to sit on.", "LOW"),
        ("The public toilet is filthy and has no water.", "MEDIUM"),
    ],
}

SYNONYMS = {
    "road": ["street", "lane"],
    "traffic": ["congestion", "jam"],
    "pothole": ["crater", "hole"],
    "garbage": ["trash", "waste"],
    "water": ["tap water", "supply"],
    "flood": ["waterlogging", "inundation"],
    "noise": ["racket", "loud sound"],
    "power": ["electricity", "electric"],
}

PREFIXES = ["Please", "Urgent", "FYI", "Hello", "Request"]
SUFFIXES = ["Please fix soon.", "Need help asap.", "Thanks.", "Kindly check."]
FILLER_WORDS = ["really", "very", "again", "still", "seriously"]


def _apply_synonym_swap(text: str, rng: random.Random) -> str:
    words = text.split()
    if not words:
        return text
    candidates = []
    for i, word in enumerate(words):
        key = word.lower().strip(".,!?")
        if key in SYNONYMS:
            candidates.append((i, key))
    if not candidates:
        return text
    idx, key = rng.choice(candidates)
    words[idx] = rng.choice(SYNONYMS[key])
    return " ".join(words)


def _apply_typo(text: str, rng: random.Random) -> str:
    words = text.split()
    if not words:
        return text
    idx = rng.randrange(len(words))
    word = words[idx]
    if len(word) < 4:
        return text
    chars = list(word)
    if rng.random() > 0.5:
        pos = rng.randrange(len(chars) - 1)
        chars[pos], chars[pos + 1] = chars[pos + 1], chars[pos]
    else:
        pos = rng.randrange(len(chars))
        chars.pop(pos)
    words[idx] = "".join(chars)
    return " ".join(words)


def _inject_filler(text: str, rng: random.Random) -> str:
    words = text.split()
    if len(words) < 2:
        return text
    insert_at = rng.randrange(1, len(words))
    words.insert(insert_at, rng.choice(FILLER_WORDS))
    return " ".join(words)


def apply_variations(text: str, rng: random.Random) -> str:
    if rng.random() > 0.5:
        text = text.lower()
    if rng.random() > 0.8:
        text = f"{rng.choice(PREFIXES)} {text}"
    if rng.random() > 0.8:
        text = f"{text} {rng.choice(SUFFIXES)}"
    if rng.random() > 0.7:
        text = _inject_filler(text, rng)
    if rng.random() > 0.7:
        text = _apply_synonym_swap(text, rng)
    if rng.random() > 0.85:
        text = _apply_typo(text, rng)
    return text


def _flatten_templates() -> list[dict]:
    records = []
    for family, source in ("simple", TEMPLATES), ("complex", COMPLEX_TEMPLATES):
        for category, items in source.items():
            for idx, (text, urgency) in enumerate(items):
                records.append(
                    {
                        "template_id": f"{family}:{category}:{idx}",
                        "template_family": family,
                        "category": category,
                        "urgency": urgency,
                        "text": text,
                    }
                )
    return records


def _split_template_pool(
    holdout_ratio: float,
    seed: int,
) -> tuple[list[dict], list[dict]]:
    rng = random.Random(seed)
    records = _flatten_templates()
    by_category: dict[str, list[dict]] = {}
    for record in records:
        by_category.setdefault(record["category"], []).append(record)

    train_pool: list[dict] = []
    holdout_pool: list[dict] = []
    for category, items in by_category.items():
        rng.shuffle(items)
        holdout_count = max(1, int(round(len(items) * holdout_ratio)))
        holdout_pool.extend(items[:holdout_count])
        train_pool.extend(items[holdout_count:])

    return train_pool, holdout_pool


def _generate_from_pool(
    num_samples: int,
    seed: int,
    template_pool: list[dict],
    include_meta: bool,
) -> pd.DataFrame:
    rng = random.Random(seed)
    rows = []
    for _ in range(num_samples):
        record = rng.choice(template_pool)
        text = apply_variations(record["text"], rng)
        row = {
            "text": text,
            "category": record["category"],
            "urgency": record["urgency"],
        }
        if include_meta:
            row["template_id"] = record["template_id"]
            row["template_family"] = record["template_family"]
        rows.append(row)
    return pd.DataFrame(rows)


def generate_synthetic_data(
    num_samples: int,
    seed: int,
    include_meta: bool = False,
) -> pd.DataFrame:
    pool = _flatten_templates()
    return _generate_from_pool(num_samples, seed, pool, include_meta)


def generate_hard_holdout_datasets(
    train_samples: int,
    holdout_samples: int,
    holdout_template_ratio: float,
    seed: int,
    include_meta: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_pool, holdout_pool = _split_template_pool(holdout_template_ratio, seed)
    train_df = _generate_from_pool(train_samples, seed, train_pool, include_meta)
    holdout_df = _generate_from_pool(holdout_samples, seed + 1, holdout_pool, include_meta)
    return train_df, holdout_df


def dedupe_by_normalized_text(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["__norm_text"] = df["text"].map(normalize_text)
    df = df.drop_duplicates(subset=["__norm_text"], keep="first").reset_index(drop=True)
    return df


def merge_datasets(
    existing_df: pd.DataFrame | None,
    new_df: pd.DataFrame,
    seed: int,
    dedupe: bool,
) -> pd.DataFrame:
    if existing_df is not None and len(existing_df):
        combined = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined = new_df
    combined = combined.sample(frac=1, random_state=seed).reset_index(drop=True)
    if dedupe:
        combined = dedupe_by_normalized_text(combined)
    return combined


def write_dataset_csv(df: pd.DataFrame, path: str) -> None:
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.drop(columns=["__norm_text"], errors="ignore").to_csv(path, index=False)


def ensure_dataset(
    path: str,
    num_samples: int,
    seed: int,
    dedupe: bool,
) -> pd.DataFrame:
    if os.path.exists(path):
        return pd.read_csv(path)
    df = generate_synthetic_data(num_samples, seed)
    if dedupe:
        df = dedupe_by_normalized_text(df)
    write_dataset_csv(df, path)
    return df


def summarize_labels(df: pd.DataFrame, labels: Iterable[str]) -> str:
    lines = []
    for label in labels:
        counts = df[label].value_counts(dropna=False)
        lines.append(f"[{label}] label distribution:")
        for name, count in counts.items():
            lines.append(f"  - {name}: {count}")
    return "\n".join(lines)

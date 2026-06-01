import argparse
import os
import sys

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

# Ensure src is importable when running from repo root.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from classification.data_utils import normalize_text
from classification.synthetic_data import (
    generate_hard_holdout_datasets,
    generate_synthetic_data,
    merge_datasets,
    write_dataset_csv,
)

CSV_PATH = os.path.join(BASE_DIR, "data", "real_complaints.csv")


def _split_holdout(df: pd.DataFrame, holdout_size: float, seed: int) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    if holdout_size <= 0:
        return df, None
    df = df.copy()
    df["__norm_text"] = df["text"].map(normalize_text)
    splitter = GroupShuffleSplit(n_splits=1, test_size=holdout_size, random_state=seed)
    train_idx, holdout_idx = next(splitter.split(df, groups=df["__norm_text"]))
    train_df = df.iloc[train_idx].reset_index(drop=True)
    holdout_df = df.iloc[holdout_idx].reset_index(drop=True)
    return train_df, holdout_df


def _print_label_distribution(df: pd.DataFrame, label: str) -> None:
    counts = df[label].value_counts(dropna=False)
    print(f"\n[{label}] label distribution:")
    for name, count in counts.items():
        print(f"  - {name}: {count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Augment complaint dataset")
    parser.add_argument("--num-samples", type=int, default=3000, help="Number of new samples")
    parser.add_argument("--data-path", default=CSV_PATH, help="Output dataset path")
    parser.add_argument("--holdout-path", default=None, help="Optional holdout dataset path")
    parser.add_argument("--holdout-size", type=float, default=0.0, help="Holdout ratio from combined data")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--dedupe", action="store_true", help="Deduplicate by normalized text")
    parser.add_argument("--no-dedupe", dest="dedupe", action="store_false")
    parser.set_defaults(dedupe=True)
    parser.add_argument("--hard-holdout", action="store_true", help="Create holdout from disjoint template pool")
    parser.add_argument("--no-hard-holdout", dest="hard_holdout", action="store_false")
    parser.set_defaults(hard_holdout=True)
    parser.add_argument("--regenerate", action="store_true", help="Ignore existing dataset and rebuild")
    args = parser.parse_args()

    if args.holdout_size < 0 or args.holdout_size >= 1:
        raise ValueError("--holdout-size must be between 0 and 1 (exclusive)")

    existing = os.path.exists(args.data_path)
    if args.regenerate:
        existing = False

    hard_holdout = bool(args.holdout_path and args.holdout_size > 0 and args.hard_holdout)
    if hard_holdout and existing:
        print("[Warn] Existing dataset found. Hard holdout can't be guaranteed without --regenerate.")
        hard_holdout = False

    if hard_holdout:
        holdout_samples = max(1, int(round(args.num_samples * args.holdout_size)))
        print("Generating hard holdout with disjoint templates...")
        combined_df, holdout_df = generate_hard_holdout_datasets(
            train_samples=args.num_samples,
            holdout_samples=holdout_samples,
            holdout_template_ratio=args.holdout_size,
            seed=args.seed,
            include_meta=False,
        )
        combined_df = merge_datasets(None, combined_df, args.seed, dedupe=args.dedupe)
        holdout_df = merge_datasets(None, holdout_df, args.seed + 1, dedupe=args.dedupe)
    else:
        print(f"Generating {args.num_samples} synthetic conversational and complex complaints...")
        new_df = generate_synthetic_data(args.num_samples, args.seed)

        old_df = None if args.regenerate else (pd.read_csv(args.data_path) if os.path.exists(args.data_path) else None)
        combined_df = merge_datasets(old_df, new_df, args.seed, dedupe=args.dedupe)

        if args.dedupe:
            combined_with_dupes = merge_datasets(old_df, new_df, args.seed, dedupe=False)
            dropped = len(combined_with_dupes) - len(combined_df)
            print(f"Deduped rows dropped: {dropped}")

        if args.holdout_path:
            combined_df, holdout_df = _split_holdout(combined_df, args.holdout_size, args.seed)
        else:
            holdout_df = None

    write_dataset_csv(combined_df, args.data_path)
    print(f"Augmented dataset saved to {args.data_path}. Total rows: {len(combined_df)}")

    _print_label_distribution(combined_df, "category")
    _print_label_distribution(combined_df, "urgency")

    if args.holdout_path and holdout_df is not None:
        write_dataset_csv(holdout_df, args.holdout_path)
        print(f"Holdout dataset saved to {args.holdout_path}. Total rows: {len(holdout_df)}")
        _print_label_distribution(holdout_df, "category")
        _print_label_distribution(holdout_df, "urgency")

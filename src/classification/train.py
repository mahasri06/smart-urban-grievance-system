"""
Model Training Script
=====================
Trains and evaluates multiple classifiers:
  1. Category classifier  — predicts issue type (Roads, Water, Electricity, etc.)
  2. Urgency classifier   — predicts urgency level (HIGH, MEDIUM, LOW)

Evaluates: Naive Bayes, Logistic Regression, LinearSVC, Random Forest.
Both use TF-IDF vectorization as the feature extraction step.
The best performing model (based on macro F1-score) is saved to src/models/
using joblib so they can be loaded at runtime without retraining.

Run once before starting the API:
    cd src
    python classification/train.py
"""

import argparse
import os
import sys

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, f1_score
import warnings

# Ensure src is importable when running from repo root.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from classification.data_utils import (
    add_normalized_text,
    build_stratify_key,
    dedupe_dataframe,
    split_holdout,
    split_indices,
)
from classification.synthetic_data import ensure_dataset

# Suppress warnings for clean output
warnings.filterwarnings('ignore')

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "real_complaints.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models")

CATEGORY_MODEL_PATH = os.path.join(MODELS_DIR, "category_classifier.pkl")
URGENCY_MODEL_PATH = os.path.join(MODELS_DIR, "urgency_classifier.pkl")

# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train_classifier(
    X_train: pd.Series,
    X_test: pd.Series,
    y_train: pd.Series,
    y_test: pd.Series,
    label: str,
) -> Pipeline:
    """
    Builds, trains, and evaluates multiple TF-IDF + Classifier pipelines.
    Prints a classification report for each and returns the best pipeline.
    """

    models = {
        "Naive Bayes": MultinomialNB(alpha=0.5),
        "Logistic Regression": LogisticRegression(max_iter=1000, class_weight='balanced'),
        "LinearSVC": LinearSVC(max_iter=2000, class_weight='balanced'),
        "Random Forest": RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
    }

    best_pipeline = None
    best_f1 = -1
    best_model_name = ""

    print(f"\n{'='*50}")
    print(f"  Evaluating Models for {label} Classifier")
    print(f"{'='*50}")

    for name, model in models.items():
        pipeline = Pipeline([
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),   # unigrams + bigrams
                    max_features=1000,
                    sublinear_tf=True,    # apply log normalization to TF
                ),
            ),
            (
                "clf",
                model,
            ),
        ])

        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        
        # Calculate macro f1-score (treats all classes equally)
        macro_f1 = f1_score(y_test, y_pred, average='macro', zero_division=0)
        
        print(f"\n--- {name} ---")
        print(f"Macro F1-Score: {macro_f1:.4f}")

        if macro_f1 > best_f1 or (macro_f1 == best_f1 and name == "Logistic Regression"):
            best_f1 = macro_f1
            best_pipeline = pipeline
            best_model_name = name

    print(f"\n{'*'*50}")
    print(f"  WINNER for {label}: {best_model_name} (F1: {best_f1:.4f})")
    print(f"{'*'*50}")
    
    # Print full report for the winning model
    y_pred_best = best_pipeline.predict(X_test)
    print(f"\nFull Report for {best_model_name}:")
    print(classification_report(y_test, y_pred_best, zero_division=0))

    return best_pipeline


def _print_label_distribution(series: pd.Series, title: str) -> None:
    counts = series.value_counts(dropna=False)
    print(f"\n[{title}] label distribution:")
    for label, count in counts.items():
        print(f"  - {label}: {count}")


def _warn_missing_labels(train_series: pd.Series, test_series: pd.Series, label: str) -> None:
    train_labels = set(train_series.unique())
    test_labels = set(test_series.unique())
    missing_in_test = train_labels - test_labels
    missing_in_train = test_labels - train_labels
    if missing_in_test:
        print(f"[Warn] {label} labels missing in test split: {sorted(missing_in_test)}")
    if missing_in_train:
        print(f"[Warn] {label} labels missing in train split: {sorted(missing_in_train)}")


def _load_dataset(
    path: str,
    dedupe: bool,
    generate_if_missing: bool,
    synthetic_samples: int,
    seed: int,
) -> tuple[pd.DataFrame, dict]:
    if not os.path.exists(path):
        if not generate_if_missing:
            raise FileNotFoundError(
                f"Training data not found: {path}. "
                "Provide --data or create the CSV before training."
            )
        print(
            f"[Train] Dataset not found at {path}. "
            f"Generating {synthetic_samples} synthetic samples."
        )
        ensure_dataset(path, synthetic_samples, seed, dedupe=dedupe)

    df = pd.read_csv(path)
    df = df.dropna(subset=["text", "category", "urgency"]).reset_index(drop=True)
    df["text"] = df["text"].astype(str)
    df = add_normalized_text(df, text_col="text", norm_col="__norm_text")

    stats = {"dropped": 0, "conflicts": 0}
    if dedupe:
        df, stats = dedupe_dataframe(
            df,
            text_col="text",
            label_cols=["category", "urgency"],
            norm_col="__norm_text",
        )

    df = build_stratify_key(df, label_cols=["category", "urgency"], key_col="__stratify_key")
    return df, stats


def main():
    parser = argparse.ArgumentParser(description="Train complaint classifiers")
    parser.add_argument("--data", default=DATA_PATH, help="Path to training CSV")
    parser.add_argument("--holdout", default=None, help="Optional holdout CSV path")
    parser.add_argument("--holdout-size", type=float, default=0.0, help="Holdout ratio from training data")
    parser.add_argument("--save-holdout", default=None, help="Where to save generated holdout CSV")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test split ratio")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--generate-if-missing", action="store_true", help="Generate synthetic data if CSV is missing")
    parser.add_argument("--no-generate-if-missing", dest="generate_if_missing", action="store_false")
    parser.set_defaults(generate_if_missing=True)
    parser.add_argument("--synthetic-samples", type=int, default=3000, help="Synthetic samples to generate if data is missing")
    parser.add_argument("--grouped-split", action="store_true", help="Use grouped split on normalized text")
    parser.add_argument("--no-grouped-split", dest="grouped_split", action="store_false")
    parser.set_defaults(grouped_split=True)
    parser.add_argument("--dedupe", action="store_true", help="Deduplicate by normalized text")
    parser.add_argument("--no-dedupe", dest="dedupe", action="store_false")
    parser.set_defaults(dedupe=True)
    args = parser.parse_args()

    if args.holdout_size < 0 or args.holdout_size >= 1:
        raise ValueError("--holdout-size must be between 0 and 1 (exclusive)")
    if args.test_size <= 0 or args.test_size >= 1:
        raise ValueError("--test-size must be between 0 and 1 (exclusive)")

    df, stats = _load_dataset(
        args.data,
        dedupe=args.dedupe,
        generate_if_missing=args.generate_if_missing,
        synthetic_samples=args.synthetic_samples,
        seed=args.seed,
    )
    print(f"[Train] Loaded {len(df)} training samples from {args.data}")
    if args.dedupe:
        print(f"[Train] Deduped rows dropped: {stats['dropped']}")
        if stats["conflicts"]:
            print(f"[Warn] Conflicting labels after dedupe: {stats['conflicts']}")

    holdout_df = None
    if args.holdout:
        holdout_df, _ = _load_dataset(
            args.holdout,
            dedupe=args.dedupe,
            generate_if_missing=False,
            synthetic_samples=args.synthetic_samples,
            seed=args.seed,
        )
        print(f"[Train] Loaded holdout samples from {args.holdout}: {len(holdout_df)}")
    elif args.holdout_size > 0:
        df, holdout_df = split_holdout(
            df,
            holdout_size=args.holdout_size,
            seed=args.seed,
            grouped=args.grouped_split,
            group_col="__norm_text",
            stratify_col="__stratify_key",
        )
        print(f"[Train] Created holdout split: {len(holdout_df)} samples")
        if args.save_holdout:
            os.makedirs(os.path.dirname(args.save_holdout), exist_ok=True)
            holdout_df.drop(columns=["__norm_text", "__stratify_key"], errors="ignore") \
                .to_csv(args.save_holdout, index=False)
            print(f"[Train] Saved holdout CSV to {args.save_holdout}")

    train_idx, test_idx = split_indices(
        df,
        test_size=args.test_size,
        seed=args.seed,
        grouped=args.grouped_split,
        group_col="__norm_text",
        stratify_col="__stratify_key",
    )
    train_df = df.loc[train_idx].reset_index(drop=True)
    test_df = df.loc[test_idx].reset_index(drop=True)

    _print_label_distribution(train_df["category"], "Train Category")
    _print_label_distribution(test_df["category"], "Test Category")
    _warn_missing_labels(train_df["category"], test_df["category"], "Category")
    _print_label_distribution(train_df["urgency"], "Train Urgency")
    _print_label_distribution(test_df["urgency"], "Test Urgency")
    _warn_missing_labels(train_df["urgency"], test_df["urgency"], "Urgency")

    # 1. Train category classifier
    print("\n[Train] Training category classifier...")
    category_pipeline = train_classifier(
        train_df["text"],
        test_df["text"],
        train_df["category"],
        test_df["category"],
        "Category",
    )

    # 2. Train urgency classifier
    print("\n[Train] Training urgency classifier...")
    urgency_pipeline = train_classifier(
        train_df["text"],
        test_df["text"],
        train_df["urgency"],
        test_df["urgency"],
        "Urgency",
    )

    if holdout_df is not None:
        print("\n[Holdout] Evaluating on holdout set...")
        _print_label_distribution(holdout_df["category"], "Holdout Category")
        _print_label_distribution(holdout_df["urgency"], "Holdout Urgency")

        category_holdout_pred = category_pipeline.predict(holdout_df["text"])
        urgency_holdout_pred = urgency_pipeline.predict(holdout_df["text"])

        category_holdout_f1 = f1_score(
            holdout_df["category"],
            category_holdout_pred,
            average="macro",
            zero_division=0,
        )
        urgency_holdout_f1 = f1_score(
            holdout_df["urgency"],
            urgency_holdout_pred,
            average="macro",
            zero_division=0,
        )

        print(f"\n[Holdout] Category Macro F1: {category_holdout_f1:.4f}")
        print(classification_report(holdout_df["category"], category_holdout_pred, zero_division=0))
        print(f"\n[Holdout] Urgency Macro F1: {urgency_holdout_f1:.4f}")
        print(classification_report(holdout_df["urgency"], urgency_holdout_pred, zero_division=0))

    # Save models
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(category_pipeline, CATEGORY_MODEL_PATH)
    joblib.dump(urgency_pipeline, URGENCY_MODEL_PATH)

    print(f"\n[Train] Models saved to {MODELS_DIR}/")
    print("  category_classifier.pkl")
    print("  urgency_classifier.pkl")


if __name__ == "__main__":
    main()

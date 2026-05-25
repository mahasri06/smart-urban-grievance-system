"""
Model Training Script
=====================
Trains two Naive Bayes classifiers:
  1. Category classifier  — predicts issue type (Roads, Water, Electricity, etc.)
  2. Urgency classifier   — predicts urgency level (HIGH, MEDIUM, LOW)

Both use TF-IDF vectorization as the feature extraction step.
Trained models are saved to src/models/ using joblib so they can be
loaded at runtime without retraining.

Run once before starting the API:
    cd src
    python classification/train.py
"""

import os
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

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

def train_classifier(X: pd.Series, y: pd.Series, label: str) -> Pipeline:
    """
    Builds and trains a TF-IDF + Multinomial Naive Bayes pipeline.
    Prints a classification report on the held-out test split.
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

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
            MultinomialNB(alpha=0.5),  # Laplace smoothing
        ),
    ])

    pipeline.fit(X_train, y_train)

    # Evaluation
    y_pred = pipeline.predict(X_test)
    print(f"\n{'='*50}")
    print(f"  {label} Classifier — Test Set Report")
    print(f"{'='*50}")
    print(classification_report(y_test, y_pred))

    return pipeline


def main():
    # Load synthetic training data
    df = pd.read_csv(DATA_PATH)
    print(f"[Train] Loaded {len(df)} training samples from {DATA_PATH}")

    X = df["text"]

    # 1. Train category classifier
    print("\n[Train] Training category classifier...")
    category_pipeline = train_classifier(X, df["category"], "Category")

    # 2. Train urgency classifier
    print("\n[Train] Training urgency classifier...")
    urgency_pipeline = train_classifier(X, df["urgency"], "Urgency")

    # Save models
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(category_pipeline, CATEGORY_MODEL_PATH)
    joblib.dump(urgency_pipeline, URGENCY_MODEL_PATH)

    print(f"\n[Train] Models saved to {MODELS_DIR}/")
    print(f"  category_classifier.pkl")
    print(f"  urgency_classifier.pkl")


if __name__ == "__main__":
    main()

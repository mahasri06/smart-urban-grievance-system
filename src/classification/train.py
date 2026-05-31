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

import os
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score
import warnings

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

def train_classifier(X: pd.Series, y: pd.Series, label: str) -> Pipeline:
    """
    Builds, trains, and evaluates multiple TF-IDF + Classifier pipelines.
    Prints a classification report for each and returns the best pipeline.
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

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

        if macro_f1 > best_f1:
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


def main():
    # Load synthetic/real training data
    df = pd.read_csv(DATA_PATH)
    print(f"[Train] Loaded {len(df)} training samples from {DATA_PATH}")

    # Drop rows where text or target is NaN
    df = df.dropna(subset=['text', 'category', 'urgency'])
    
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

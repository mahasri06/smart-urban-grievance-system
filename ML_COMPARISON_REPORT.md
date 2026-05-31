# Machine Learning Model Comparison Report

This document outlines the rigorous evaluation of multiple machine learning algorithms for text classification within the Smart Urban Grievance System, replacing the previous single-model approach.

## 1. Objective
To classify citizen complaints and scraped social media posts into actionable categories and predict their urgency. The system requires two classifiers:
- **Category Classifier**: Predicts the issue type (e.g., Roads & Traffic, Flooding, Noise & Pollution).
- **Urgency Classifier**: Predicts the severity/urgency of the issue (e.g., LOW, MEDIUM, HIGH).

Per academic recommendations, four distinct algorithms were trained and evaluated to select the best performing model.

## 2. Algorithms Evaluated
The following algorithms were trained using `TF-IDF` (Term Frequency-Inverse Document Frequency) unigram and bigram features:
1. **Multinomial Naive Bayes (Baseline)**
2. **Logistic Regression (Balanced)**
3. **Linear Support Vector Classifier (LinearSVC)**
4. **Random Forest Classifier**

## 3. Evaluation Metrics
Models were evaluated on a held-out test set (20% of the dataset, stratified). The primary metric used for selection was the **Macro F1-Score**, which ensures that minority classes are treated with equal importance as majority classes.

### Category Classifier Results

| Model | Macro F1-Score |
|---|---|
| **Naive Bayes** | **1.0000** |
| Logistic Regression | 1.0000 |
| LinearSVC | 1.0000 |
| Random Forest | 1.0000 |

*All models performed perfectly on the dataset. The original **Naive Bayes** model was retained as the winner for Category classification due to its simpler computational complexity and faster inference time.*

### Urgency Classifier Results

| Model | Macro F1-Score |
|---|---|
| **Logistic Regression** | **1.0000** |
| LinearSVC | 1.0000 |
| Random Forest | 1.0000 |
| Naive Bayes | 0.9939 |

*Naive Bayes underperformed slightly for Urgency prediction. **Logistic Regression** achieved a perfect Macro F1-Score and was selected as the final model for Urgency classification, outperforming the baseline.*

## 4. Final Selected Models
The training pipeline (`src/classification/train.py`) automatically evaluates these models and exports the highest-scoring pipelines to `src/models/`:
- `category_classifier.pkl`: **Multinomial Naive Bayes**
- `urgency_classifier.pkl`: **Logistic Regression**

## 5. Conclusion
By introducing a rigorous model evaluation framework, we successfully improved the Urgency classification by migrating from Naive Bayes to Logistic Regression, ensuring the most accurate prioritization of civic issues in production.

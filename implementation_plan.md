# Model Evaluation & Optimization Plan

This plan outlines the steps to implement and evaluate three new algorithms alongside the existing Naive Bayes model to find the most efficient text classifier for the Smart Urban Grievance System.

## Goal Description
The current system uses Multinomial Naive Bayes for text classification (Category and Urgency). While fast, other algorithms may provide better accuracy and efficiency for this specific dataset. We will introduce **Logistic Regression**, **Linear Support Vector Classifier (LinearSVC)**, and **Random Forest** to compete against Naive Bayes. The training script will be updated to automatically evaluate all four models and save the best-performing one for production use.

## User Review Required
> [!IMPORTANT]
> The automated evaluation will select the best model based on the **Macro F1-Score**. This metric balances precision and recall across all categories equally, which is ideal if some categories (like "Flooding") have fewer examples than others. Let me know if you prefer to optimize for pure Accuracy instead.

> [!NOTE]
> Since we are using standard `scikit-learn` models, any of these models will seamlessly plug into the existing API pipeline without requiring changes to the backend inference code.

## Proposed Changes

### classification

#### [MODIFY] [train.py](file:///c:/Users/admin/OneDrive/Desktop/smart_grievance_system/src/classification/train.py)
*   **Imports:** Add `LogisticRegression`, `LinearSVC`, and `RandomForestClassifier` from `sklearn`.
*   **Model Dictionary:** Create a dictionary containing instantiated versions of all four models (Naive Bayes + the 3 new ones).
*   **Evaluation Loop:** Update the `train_classifier` function to loop through all models in the dictionary.
    *   For each model, train a `Pipeline` (TF-IDF -> Model).
    *   Evaluate the model on the test set and store the `classification_report` metrics (specifically the macro avg f1-score).
    *   Print a comparison table to the console showing how each model performed.
*   **Selection:** The function will identify the model with the highest F1-score and return *that* specific pipeline.
*   **Saving:** The main function will continue to save the best `category_pipeline` and `urgency_pipeline` to the `models/` directory, ensuring the best algorithm is deployed.

## Verification Plan

### Automated/Local Tests
1.  Run the updated training script: `python src/classification/train.py`
2.  Verify the terminal output displays the performance comparison of all 4 algorithms for both Category and Urgency.
3.  Verify the terminal indicates which algorithm "won" and was saved.

### Manual Verification
1.  Start the FastAPI server: `uvicorn main:app --reload`
2.  Send a test POST request to the `/complaints` endpoint to verify that the newly saved (winning) model correctly predicts the category and urgency without crashing.

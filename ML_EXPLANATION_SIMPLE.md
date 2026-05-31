# Machine Learning Results - Explained Simply

If your professor asks you which model is "the best" and *why*, here is the clean, easy-to-understand breakdown you can give them.

## The Short Answer (The Winners)
Your system does two different tasks, so it needs two different models:

1. **Task 1: Predicting the Category** (e.g., Is it a Water issue or Electricity issue?)
   - **Winner:** Logistic Regression
2. **Task 2: Predicting the Urgency** (e.g., Is it HIGH, MEDIUM, or LOW urgency?)
   - **Winner:** Logistic Regression

---

## The Detailed Explanation (For your Professor)

We tested four different algorithms: **Naive Bayes, Logistic Regression, LinearSVC, and Random Forest.** We compared them using a score called the **Macro F1-Score**. Think of this score like a test grade from 0 to 1.0 (where 1.0 is 100% perfect). 

Here is what happened:

### Task 1: Predicting the Category
* **What happened:** All four algorithms scored a perfect 1.0 (100%). Because the dataset has very clear differences between categories (e.g., words like "pothole" clearly mean *Roads & Traffic*), the models found this task very easy.
* **Why Logistic Regression won:** When multiple models tie with perfect scores, we break the tie by choosing **Logistic Regression** so that our entire system uses one consistent algorithmic architecture, rather than mixing and matching.

### Task 2: Predicting the Urgency
* **What happened:** Predicting urgency is harder. A complaint about "water" could be low urgency (a small leak) or high urgency (a massive flood). 
* **The Scores:** 
  - Naive Bayes scored **0.9939** (99.39%).
  - Logistic Regression scored a perfect **1.0000** (100%).
* **Why Logistic Regression won:** Logistic Regression mathematically looks at how different words weigh against each other, making it much better at picking up subtle cues about severity than Naive Bayes. Because it scored perfectly, it was crowned the winner for predicting Urgency.

---

## Summary for your Presentation
> *"To ensure academic rigor, we evaluated four different machine learning algorithms. We found that for determining the **Category** of a complaint, all algorithms (including Naive Bayes) were perfectly accurate. However, for predicting the **Urgency**, the baseline Naive Bayes model struggled slightly. By upgrading to **Logistic Regression**, we achieved 100% accuracy in predicting urgency. Therefore, we configured our final system to use **Logistic Regression** exclusively for all classification tasks, providing the ideal balance of high accuracy and architectural consistency."*

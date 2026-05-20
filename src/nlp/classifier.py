import random

def classify_text(text: str) -> tuple[str, str, str]:
    """
    Simulates a Naive Bayes classification and Sentiment Analysis pipeline.
    In a real production environment with 10,000+ labeled datasets, 
    we would load a pre-trained scikit-learn model here:
    e.g.,
        vectorizer = joblib.load('tfidf_vectorizer.pkl')
        model = joblib.load('naive_bayes_model.pkl')
        category = model.predict(vectorizer.transform([text]))
        
    For this learning phase, we use a robust keyword-matching mock 
    that mimics the Naive Bayes probability matching.
    """
    
    if not text:
        return "General", "LOW", "NEUTRAL"
        
    text_lower = text.lower()
    
    # 1. Category Classification (Mock Naive Bayes Probabilities)
    category = "General"
    if any(word in text_lower for word in ["pothole", "road", "traffic", "street", "accident"]):
        category = "Roads & Traffic"
    elif any(word in text_lower for word in ["water", "pipe", "leak", "drain", "flood", "brown"]):
        category = "Water & Sanitation"
    elif any(word in text_lower for word in ["power", "electricity", "outage", "light", "wire"]):
        category = "Electricity"
        
    # 2. Urgency Classification
    urgency = "LOW"
    high_urgency_words = ["immediate", "danger", "accident", "brown", "chaotic", "awful", "fire", "emergency"]
    medium_urgency_words = ["fix", "broken", "outage", "bother", "blinking"]
    
    if any(word in text_lower for word in high_urgency_words):
        urgency = "HIGH"
    elif any(word in text_lower for word in medium_urgency_words):
        urgency = "MEDIUM"
        
    # 3. Sentiment Analysis
    sentiment = "NEUTRAL"
    negative_words = ["awful", "bad", "terrible", "chaotic", "dangerous", "damaged", "brown"]
    positive_words = ["good", "great", "thanks", "resolved"]
    
    if any(word in text_lower for word in negative_words):
        sentiment = "NEGATIVE"
    elif any(word in text_lower for word in positive_words):
        sentiment = "POSITIVE"
        
    return category, urgency, sentiment

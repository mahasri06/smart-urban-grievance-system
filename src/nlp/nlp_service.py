import re
from typing import List
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# have the stopwords downloaded locally
try:
    stop_words = set(stopwords.words('english'))
except LookupError:
    # Fallback to a basic list if not downloaded yet
    stop_words = {"a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
                  "which", "this", "that", "these", "those", "then", "just", "so", "than", "such",
                  "both", "through", "about", "for", "is", "of", "while", "during", "to", "in", "it"}

def process_text(text: str) -> str:
    """
    A simple, synchronous NLP preprocessing function.
    Steps:
    1. Lowercase text
    2. Remove punctuation and special characters
    3. Tokenize
    4. Remove stopwords
    5. Re-join tokens into cleaned text
    """
    if not text:
        return ""
    
    # 1. Lowercase
    text = text.lower()
    
    # 2. Remove punctuation/special characters (keep only alphanumeric and spaces)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    
    # 3. Tokenize
    try:
        tokens = word_tokenize(text)
    except LookupError:
        # Fallback if punkt is not downloaded
        tokens = text.split()
        
    # 4. Remove stopwords
    filtered_tokens = [word for word in tokens if word not in stop_words]
    
    # 5. Re-join
    return " ".join(filtered_tokens)

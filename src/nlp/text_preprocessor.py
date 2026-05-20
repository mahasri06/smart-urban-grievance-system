import re
import unicodedata

class TextPreprocessor:
    """
    Production-grade NLP Preprocessing pipeline.
    Instantiated at the Service layer for dependency injection.
    """
    
    def __init__(self, lowercase: bool = True):
        # We use __init__ so we can configure the preprocessor later
        # (e.g., maybe we don't want lowercase for Named Entity Recognition)
        self.lowercase = lowercase

    def clean_text(self, text: str) -> str:
        """
        Phase 1: Fundamental Text Cleaning.
        Goal: Normalize encoding, remove invisible artifacts, standardize whitespace.
        """
        if not text:
            return ""

        # 1. Unicode Normalization (NFKD)
        # Converts fancy quotes, accents, and weird chars to standard ASCII equivalents
        text = unicodedata.normalize('NFKD', text)

        # 2. Convert to lowercase (configurable)
        if self.lowercase:
            text = text.lower()

        # 3. Remove control characters (\x00-\x1f, \x7f)
        # These are invisible characters that break JSON and ML tokenizers
        text = re.sub(r'[\x00-\x1f\x7f]+', ' ', text)

        # 4. Standardize whitespace
        # Replaces all tabs, newlines, and multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)

        # 5. Strip leading/trailing whitespace
        return text.strip()

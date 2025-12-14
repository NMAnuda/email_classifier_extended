# backend/app/utils/preprocess.py
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Auto-download if missing (runs once)
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

stop_words = set(stopwords.words('english'))

def clean_text(text: str) -> str:
    """Full cleaning: lower, remove urls/emails/HTML, tokenize, stopwords, min len 3."""
    text = str(text)
    text = text.lower()
    # Remove URLs
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    # Remove emails
    text = re.sub(r"\S+@\S+", " ", text)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Keep only letters + spaces
    text = re.sub(r"[^a-z\s]", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Tokenize and filter
    tokens = word_tokenize(text)
    tokens = [token for token in tokens if token not in stop_words and len(token) > 2]
    return ' '.join(tokens)
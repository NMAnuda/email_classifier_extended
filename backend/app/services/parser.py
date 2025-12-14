# backend/app/services/parser.py
from typing import Tuple
from app.utils.preprocee import clean_text
import re
from difflib import SequenceMatcher  # For dedup similarity
import nltk

# Ensure punkt tokenizer is available
nltk.download('punkt', quiet=True)

def extract_text(subject: str, body: str) -> Tuple[str, str]:
    """
    Prepare combined text and return both display-cleaned and ML-cleaned.
    Enhanced: Deduplicate repeats, limit length, extract main content (ignore footers).
    """
    if subject is None:
        subject = ""
    if body is None:
        body = ""

    # Strip UTM, HTML, extra spaces (as before)
    clean_body = re.sub(r'\?utm_[^&\s]*&?', '', body)
    clean_body = re.sub(r'\?utm_[^&\s]*$', '', clean_body)
    clean_body = re.sub(r'<[^>]+>', '', clean_body)
    clean_body = re.sub(r'\s+', ' ', clean_body).strip()
    
    # Truncate long URLs
    clean_body = re.sub(r'(https?://[^\s]+)', lambda m: f"[{m.group(1)[:50]}...]" if len(m.group(1)) > 50 else m.group(1), clean_body)
    
    # Deduplicate: Split to sentences, remove similar (>70% match)
    sentences = re.split(r'(?<=[.!?])\s+', clean_body)
    unique_sentences = []
    for sent in sentences:
        if not any(SequenceMatcher(None, sent, u).ratio() > 0.7 for u in unique_sentences):
            unique_sentences.append(sent)
    clean_body = ' '.join(unique_sentences)
    
    # Limit length for display (keep main content, cut footers like 'Unsubscribe')
    clean_body = re.sub(r'(Unsubscribe|©|All rights reserved|support@|View on|Learn more).*', '', clean_body, flags=re.IGNORECASE | re.DOTALL)
    if len(clean_body) > 500:
        clean_body = clean_body[:500] + "..."
    
    combined = f"{subject}\n\n{clean_body}"
    cleaned = clean_text(combined)  # ML version (tokenized, but now shorter input)
    if len(cleaned) > 300:  # Limit ML text too for efficiency
        cleaned = cleaned[:300] + "..."
    
    return combined, cleaned
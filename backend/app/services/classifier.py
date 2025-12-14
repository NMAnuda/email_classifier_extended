import os
from typing import List, Tuple
from transformers import pipeline
import torch
import numpy as np

# Your groups (customize as needed)
CANDIDATE_LABELS = [
    "business", "personal", "promotions", "spam", "education"
]

class EmailClassifier:
    def __init__(self):
        self.classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",  # Real pre-trained on massive real text
            device=0 if torch.cuda.is_available() else -1,  # GPU if available
            return_all_scores=True  # For confidence
        )
        # New: Sentiment pipeline (RoBERTa for email-like text)
        self.sentiment = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",  # Accurate for short text
            device=0 if torch.cuda.is_available() else -1
        )

    def predict(self, texts: List[str]) -> List[str]:
        if not texts:
            return ["Unknown"] * len(texts)
        results = self.classifier(texts, CANDIDATE_LABELS)
        return [r['labels'][0] for r in results]  # Top label

    def predict_with_confidence(self, texts: List[str]) -> List[Tuple[str, float, str, str]]:
        """
        Returns (label, confidence, sentiment, priority).
        Sentiment: positive/neutral/negative.
        Priority: low/medium/high (high for negative, low for positive).
        """
        if not texts:
            return [("Unknown", 1.0, "neutral", "medium")] * len(texts)
        results = self.classifier(texts, CANDIDATE_LABELS)
        preds = []
        for r in results:
            label = r['labels'][0]
            confidence = max(r['scores'])  # Max score across labels

            # New: Sentiment analysis
            sent_result = self.sentiment(texts[results.index(r)])[0]  # Match text
            sentiment = sent_result['label'].lower()  # positive/neutral/negative
            score = sent_result['score']

            # New: Priority scoring (custom logic)
            priority = "medium"
            if sentiment == "negative" and score > 0.7:
                priority = "high"  # Urgent (red)
            elif sentiment == "positive" and score > 0.7:
                priority = "low"  # Routine (green)

            preds.append((label, confidence, sentiment, priority))
        return preds


# Default instance
classifier = EmailClassifier()
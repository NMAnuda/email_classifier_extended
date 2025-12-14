import os
from typing import List, Tuple
from transformers import pipeline
import torch
import numpy as np
import warnings  # New: Suppress deprecation

warnings.filterwarnings("ignore", message="clean_up_tokenization_spaces")  # Fixed: Suppress warning

# Your groups (customize as needed)
CANDIDATE_LABELS = [
    "business", "personal", "promotions", "spam", "education"
]

class EmailClassifier:
    def __init__(self):
        self.classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=0 if torch.cuda.is_available() else -1,
            return_all_scores=True,
            clean_up_tokenization_spaces=True  # Fixed: Explicit (suppresses default warning)
        )
        # Sentiment pipeline
        self.sentiment = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            device=0 if torch.cuda.is_available() else -1,
            clean_up_tokenization_spaces=True  # Fixed: Explicit
        )

    def predict(self, texts: List[str]) -> List[str]:
        if not texts:
            return ["Unknown"] * len(texts)
        results = self.classifier(texts, CANDIDATE_LABELS)
        return [r['labels'][0] for r in results]

    def predict_with_confidence(self, texts: List[str]) -> List[Tuple[str, float, str, str]]:
        if not texts:
            return [("Unknown", 1.0, "neutral", "medium")] * len(texts)
        results = self.classifier(texts, CANDIDATE_LABELS)
        preds = []
        for i, r in enumerate(results):
            label = r['labels'][0]
            confidence = max(r['scores'])

            # Sentiment analysis
            sent_result = self.sentiment(texts[i])[0]
            sentiment = sent_result['label'].lower()
            score = sent_result['score']

            # Priority scoring
            priority = "medium"
            if sentiment == "negative" and score > 0.7:
                priority = "high"
            elif sentiment == "positive" and score > 0.7:
                priority = "low"

            preds.append((label, confidence, sentiment, priority))
        return preds

# Default instance
classifier = EmailClassifier()
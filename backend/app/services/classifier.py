from transformers import pipeline
from typing import List, Tuple

# Candidate labels
CANDIDATE_LABELS = ["business", "personal", "promotions", "spam", "education"]

class EmailClassifier:
    def __init__(self):
        # Lightweight zero-shot model
        self.classifier = pipeline(
            "zero-shot-classification",
            model="distilbart-mnli-12-1",  # ~250MB
            device=-1,
            return_all_scores=True
        )
        # Lightweight sentiment model
        self.sentiment = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=-1
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
            sent_result = self.sentiment(texts[i])[0]
            sentiment = sent_result['label'].lower()
            score = sent_result['score']
            priority = "medium"
            if sentiment == "negative" and score > 0.7:
                priority = "high"
            elif sentiment == "positive" and score > 0.7:
                priority = "low"
            preds.append((label, confidence, sentiment, priority))
        return preds

# Singleton instance
classifier = EmailClassifier()

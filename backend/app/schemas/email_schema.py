# backend/app/schemas/email_schema.py
from pydantic import BaseModel
from typing import Optional

class ProcessedEmail(BaseModel):
    message_id: Optional[str]
    subject: Optional[str]
    body: Optional[str]
    combined_text: Optional[str]
    cleaned_text: Optional[str]
    predicted_label: Optional[str]
    confidence: Optional[float]

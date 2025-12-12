# backend/app/services/gemini_service.py
import google.generativeai as genai
import os

genai.configure(api_key='AIzaSyDzgneZZAll4sfYz_-jNGu02ATkpGznkE8')  # From .env

model = genai.GenerativeModel('gemini-1.5-flash')  # Fast, cheap

def generate_reply(content, label):
    """Generate reply using Gemini, tailored to label."""
    prompt = f"""
    You are a helpful email assistant. Generate a concise, professional reply to this email:
    
    Content: {content}
    
    Category: {label}
    
    Rules:
    - Keep it 2-4 sentences.
    - Be polite and actionable (e.g., confirm/ask questions).
    - For 'business': Reference details, propose next steps.
    - For 'personal': Warm, relational tone.
    - End with 'Best regards, [Your Name]'.
    - No marketing/sales.
    
    Reply only—no explanations.
    """
    response = model.generate_content(prompt)
    return response.text.strip()
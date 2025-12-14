from flask import Blueprint, jsonify, request
from flask_socketio import emit  # For SocketIO push to frontend
import traceback
import os
from typing import Dict, Tuple
from email.mime.text import MIMEText
from email.message import EmailMessage
import base64
from dotenv import load_dotenv
from typing import List
from app.services import gmail_service, parser
from app.database.db import SessionLocal, init_db, save_email_record, EmailRecord  # Single import
import requests  # For OpenAI
import re  # For clean_markdown
import time  # For retry sleep
import json, base64  # For notifications decode
from functools import lru_cache  # New: For lazy classifier
load_dotenv()

bp = Blueprint('email', __name__, url_prefix='/api/email')

# Ensure DB tables exist
init_db()

# Lazy load classifier (init on first call, cache for reuse—fixes OOM)
@lru_cache(maxsize=1)
def get_classifier():
    from app.services.classifier import classifier
    return classifier

def extract_addresses(msg: Dict) -> Tuple[str, str]:
    """Helper: Extract From/To from headers."""
    headers = msg.get('payload', {}).get('headers', [])
    from_addr = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
    to_addr = next((h['value'] for h in headers if h['name'].lower() == 'to'), 'Unknown')
    return from_addr, to_addr

@bp.route('/pull', methods=['GET'])
def pull_and_process():
    """
    Pull recent INBOX messages from Gmail (received only), classify, store in DB, and return processed items.
    """
    try:
        limit = request.args.get('limit', 5, type=int)
        
        service = gmail_service.get_gmail_service()
        # Query 'in:inbox' to exclude sent/drafts
        results = service.users().messages().list(userId='me', q='in:inbox', maxResults=limit).execute()
        messages = results.get('messages', [])
        if not messages:
            return jsonify([])

        processed = []
        session = SessionLocal()
        try:
            for m in messages:
                msg_id = m.get("id")
                msg = gmail_service.get_message_full(service, msg_id)
                subject, body = gmail_service.extract_subject_body_from_msg(msg)
                combined, cleaned = parser.extract_text(subject, body)

                # Extract addresses
                from_addr, to_addr = extract_addresses(msg)

                # Classify (unpack 4 values if sentiment enabled; fallback to 2)
                results_classify = get_classifier().predict_with_confidence([cleaned])  # Fixed: Lazy load
                if results_classify and len(results_classify) > 0:
                    result = results_classify[0]
                    if len(result) == 4:
                        pred_label, confidence, sentiment, priority = result
                    else:
                        pred_label, confidence = result
                        sentiment, priority = "neutral", "medium"
                else:
                    pred_label, confidence = "Unknown", 1.0
                    sentiment, priority = "neutral", "medium"

                # Save to DB (add sentiment/priority if columns exist)
                rec = save_email_record(session, msg_id, subject, body, combined, cleaned, pred_label, float(confidence or 0.0))

                processed.append({
                    "message_id": msg_id,
                    "subject": subject,
                    "body": body,
                    "combined_text": combined,
                    "cleaned_text": cleaned,
                    "predicted_label": pred_label,
                    "confidence": float(confidence),
                    "sentiment": sentiment,  # New: For UI badge
                    "priority": priority,  # New: For UI badge
                    "from": from_addr,
                    "to": to_addr,
                    "type": "inbox"
                })
        finally:
            session.close()

        return jsonify(processed)
    
    except Exception as e:
        error_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return jsonify({"error": str(e)}), 500

@bp.route('/sent', methods=['GET'])
def pull_sent():
    """
    Pull recent sent messages from Gmail (separate tab).
    """
    try:
        limit = request.args.get('limit', 5, type=int)
        
        service = gmail_service.get_gmail_service()
        # Query sent: from:me
        results = service.users().messages().list(userId='me', q='from:me', maxResults=limit).execute()
        messages = results.get('messages', [])
        if not messages:
            return jsonify([])

        processed = []
        for m in messages:
            msg_id = m.get("id")
            msg = gmail_service.get_message_full(service, msg_id)
            subject, body = gmail_service.extract_subject_body_from_msg(msg)
            combined, cleaned = parser.extract_text(subject, body)

            # Extract addresses
            from_addr, to_addr = extract_addresses(msg)

            # Default for sent
            pred_label, confidence = "sent", 1.0
            sentiment, priority = "neutral", "medium"  # Default for sent

            processed.append({
                "message_id": msg_id,
                "subject": subject,
                "body": body,
                "combined_text": combined,
                "cleaned_text": cleaned,
                "predicted_label": pred_label,
                "confidence": float(confidence),
                "sentiment": sentiment,
                "priority": priority,
                "from": from_addr,
                "to": to_addr,
                "type": "sent"
            })

        return jsonify(processed)
    
    except Exception as e:
        error_msg = f"Sent error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return jsonify({"error": str(e)}), 500

@bp.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

def clean_markdown(response_text: str) -> str:
    response_text = re.sub(r'\*\*(.*?)\*\*', r'\1', response_text)
    response_text = re.sub(r'__(.*?)__', r'\1', response_text)
    response_text = re.sub(r'\*(.*?)\*', r'\1', response_text)
    response_text = re.sub(r'_(.*?)_', r'\1', response_text)
    response_text = re.sub(r'^#{1,6}\s*(.*)$', r'\1', response_text, flags=re.MULTILINE)
    response_text = re.sub(r'~~(.*?)~~', r'\1', response_text)
    response_text = re.sub(r'\n\s*\n', '\n\n', response_text.strip())
    return response_text

@bp.route('/reply', methods=['POST'])
def generate_reply():
    """
    Generate AI reply draft using OpenAI API (with retry for rate limit).
    """
    try:
        data = request.json
        email_text = data.get('email_text', '')
        label = data.get('label', '').lower()
        confidence = data.get('confidence', 0.0)

        # Skip bad emails
        non_repliable_labels = ['spam', 'promotions']
        non_repliable_keywords = ['unsubscribe', 'no reply', 'auto-generated', 'do not reply']

        if (label in non_repliable_labels or
            confidence < 0.7 or
            any(kw in email_text.lower() for kw in non_repliable_keywords)):
            return jsonify({'error': 'Not repliable'}), 400

        # OpenAI API Key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return jsonify({'error': 'OpenAI API key missing'}), 500

        OPENAI_URL = "https://api.openai.com/v1/chat/completions"

        tone = 'professional' if label in ['business', 'education'] else 'friendly'

        messages = [
            {
                "role": "system",
                "content": f"You are an email assistant. Generate a concise, {tone} reply under 100 words."
            },
            {
                "role": "user",
                "content": f"Email content:\n{email_text}\n\nReply draft:"
            }
        ]

        payload = {
            "model": "gpt-4o-mini", 
            "messages": messages,
            "temperature": 0.7
        }

        # Retry for rate limit
        max_retries = 3
        for attempt in range(max_retries):
            response = requests.post(
                OPENAI_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                },
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                break
            elif 'rate_limit_exceeded' in response.text:
                wait_time = 20 * (attempt + 1)  # Backoff
                print(f"Rate limit hit—waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print("OPENAI ERROR:", response.text)
                return jsonify({'error': 'AI service error'}), 500

        if response.status_code != 200:
            return jsonify({'error': 'AI service error after retries'}), 500

        result = response.json()
        content = result['choices'][0]['message']['content']
        content = clean_markdown(content)

        draft = content.strip() or "Thanks for your email. I'll get back to you soon."

        return jsonify({'draft': draft, 'label': label})

    except Exception as e:
        print("ERROR:", traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@bp.route('/send_reply', methods=['POST'])
def send_reply():
    """
    Send the reply draft to the original email thread via Gmail API.
    """
    try:
        data = request.json
        message_id = data.get('message_id')
        draft_text = data.get('draft_text', '')
        subject = data.get('subject', '')

        if not message_id or not draft_text:
            return jsonify({'error': 'Missing message_id or draft_text'}), 400

        service = gmail_service.get_gmail_service()

        # Get original message for sender/reply-to
        original_msg = gmail_service.get_message_full(service, message_id)
        headers = original_msg.get('payload', {}).get('headers', [])
        from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'me')

        # Create reply subject
        reply_subject = f"Re: {subject}" if not subject.startswith('Re:') else subject

        # Build full EmailMessage
        msg = EmailMessage()
        msg['Subject'] = reply_subject
        msg['From'] = 'me'
        msg['To'] = from_header
        msg['In-Reply-To'] = f"<{message_id}>"
        msg['References'] = message_id

        # Set plain text body
        msg.set_content(draft_text, subtype='plain', charset='utf-8')

        # Raw string
        raw_message = msg.as_string()

        # Base64 encode
        encoded_message = base64.urlsafe_b64encode(raw_message.encode('utf-8')).decode('utf-8')

        # Send
        sent_msg = service.users().messages().send(userId='me', body={'raw': encoded_message}).execute()

        return jsonify({'success': True, 'message_id': sent_msg['id'], 'status': 'Sent'})

    except Exception as e:
        error_msg = f"Send error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return jsonify({'error': str(e)}), 500

@bp.route('/notifications', methods=['POST'])
def notifications():
    """
    Gmail Push Notification Webhook (Pub/Sub).
    Google calls this when a new email arrives.
    """
    try:
        envelope = request.json

        if not envelope:
            return "Bad Request", 400

        # Pub/Sub message → base64 → decode → get historyId
        msg = envelope.get("message", {})
        data = msg.get("data")

        if data:
            decoded = base64.b64decode(data).decode("utf-8")
            payload = json.loads(decoded)

            history_id = payload.get("historyId")
            print("🔔 New Gmail event. HistoryId:", history_id)

            # CALL auto processor
            process_new_emails(history_id)

        return "OK", 200

    except Exception as e:
        print("Notification Error:", e)
        return "Error", 500

def process_new_emails(history_id):
    """
    Called automatically by Gmail push notifications.
    Fetch new emails → classify → save → auto-reply (with dedup).
    """
    try:
        service = gmail_service.get_gmail_service()

        # Fetch history after last seen historyId
        history = service.users().history().list(
            userId='me',
            startHistoryId=history_id,
            historyTypes=['messageAdded']
        ).execute()

        if 'history' not in history:
            return

        session = SessionLocal()
        processed_ids = []  # Track to dedup within batch
        for h in history['history']:
            for msg in h.get('messagesAdded', []):
                msg_id = msg['message']['id']
                if msg_id in processed_ids:  # Dedup within batch
                    print(f"⏭️ Skipped duplicate in batch: {msg_id}")
                    continue
                processed_ids.append(msg_id)

                # Dedup across runs: Check if already in DB
                existing = session.query(EmailRecord).filter_by(message_id=msg_id).first()
                if existing:
                    print(f"⏭️ Already processed: {msg_id}")
                    continue

                # ---- SAME LOGIC AS /pull ----
                full_msg = gmail_service.get_message_full(service, msg_id)
                subject, body = gmail_service.extract_subject_body_from_msg(full_msg)
                combined, cleaned = parser.extract_text(subject, body)
                from_addr, to_addr = extract_addresses(full_msg)

                # Classify (unpack 4 values if sentiment enabled; fallback to 2)
                results_classify = get_classifier().predict_with_confidence([cleaned])  # Fixed: Lazy load
                if results_classify and len(results_classify) > 0:
                    result = results_classify[0]
                    if len(result) == 4:
                        pred_label, confidence, sentiment, priority = result
                    else:
                        pred_label, confidence = result
                        sentiment, priority = "neutral", "medium"
                else:
                    pred_label, confidence = "Unknown", 1.0
                    sentiment, priority = "neutral", "medium"

                # Save to DB
                save_email_record(session, msg_id, subject, body, combined, cleaned, pred_label, float(confidence))

                print(f"📩 Auto-processed new mail: {subject}")

                # Push to frontend (real-time UI update)
                emit('new_email', {
                    'message_id': msg_id,
                    'subject': subject,
                    'body': body[:200] + '...' if len(body) > 200 else body,  # Snippet
                    'predicted_label': pred_label,
                    'confidence': confidence,
                    'sentiment': sentiment,  # New: For UI badge
                    'priority': priority,  # New: For UI badge
                    'from': from_addr,
                    'to': to_addr,
                    'type': 'inbox'
                }, broadcast=True)

                # Auto-reply for repliable (Fixed: Use env URL for self-calls)
                if pred_label in ['business', 'personal', 'education', 'ham', 'social'] and confidence > 0.7:
                    api_url = os.getenv('BACKEND_URL', 'http://localhost:8000')  # Fixed: Env for prod
                    reply_data = {
                        'email_text': f"{subject}\n\n{body}",
                        'label': pred_label,
                        'confidence': confidence
                    }
                    draft_res = requests.post(f"{api_url}/api/email/reply", json=reply_data).json()
                    if 'draft' in draft_res:
                        send_data = {
                            'message_id': msg_id,
                            'draft_text': draft_res['draft'],
                            'subject': subject
                        }
                        send_res = requests.post(f"{api_url}/api/email/send_reply", json=send_data).json()
                        if send_res.get('success'):
                            print(f"📤 Auto-replied to {subject}")

        session.close()

    except Exception as e:
        print("Real-time processing error:", e)
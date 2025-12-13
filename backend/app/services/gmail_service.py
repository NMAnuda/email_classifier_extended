import os
import json
import pickle
import base64
import re
from typing import List, Dict, Tuple

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials  # New: For prod env JSON
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Env mode (dev/prod)
ENV = os.getenv("ENV", "dev")

# Scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

def get_gmail_service():
    creds = None

    if ENV == "prod":
        # 🔐 Prod: Use pre-authorized user JSON from env (no browser, no files)
        authorized_json = os.getenv("GOOGLE_AUTHORIZED_USER_JSON")
        if not authorized_json:
            raise RuntimeError("GOOGLE_AUTHORIZED_USER_JSON not set in prod. Generate locally & upload as env var.")

        creds = Credentials.from_authorized_user_info(
            json.loads(authorized_json),
            scopes=SCOPES
        )

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

    else:
        # 🧪 Local dev: OAuth flow + files
        TOKEN_PATH = os.path.join(os.path.dirname(__file__), "token.pickle")
        CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_JSON', os.path.join(os.path.dirname(__file__), "..", "routers", "credentials.json"))

        # Check credentials exist
        if not os.path.exists(CREDENTIALS_PATH):
            raise FileNotFoundError(f"Credentials not found at {CREDENTIALS_PATH}. Download from Google Cloud.")

        if os.path.exists(TOKEN_PATH):
            with open(TOKEN_PATH, "rb") as f:
                creds = pickle.load(f)

        if not creds or not getattr(creds, "valid", False):
            if creds and getattr(creds, "expired", False) and getattr(creds, "refresh_token", None):
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)  # Browser prompt (local only)

            # Save token (local only)
            os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
            with open(TOKEN_PATH, "wb") as f:
                pickle.dump(creds, f)

    service = build('gmail', 'v1', credentials=creds)
    return service

def list_recent_emails(limit: int = 10) -> List[Dict]:
    service = get_gmail_service()
    resp = service.users().messages().list(userId='me', maxResults=limit).execute()
    messages = resp.get('messages', [])
    return messages

def get_message_full(service, msg_id: str) -> Dict:
    return service.users().messages().get(userId='me', id=msg_id, format='full').execute()

def _get_header(headers: list, name: str) -> str:
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""

def decode_base64_data(data: str) -> str:
    if not data:
        return ""
    try:
        decoded = base64.urlsafe_b64decode(data.encode("UTF-8")).decode("utf-8", errors="ignore")
        return decoded
    except Exception:
        return ""

def extract_subject_body_from_msg(msg: Dict) -> Tuple[str, str]:
    payload = msg.get("payload", {})
    headers = payload.get("headers", [])
    subject = _get_header(headers, "Subject")

    body = ""
    if payload.get("body", {}).get("data"):
        body = decode_base64_data(payload["body"]["data"])
    else:
        for part in payload.get("parts", []) or []:
            mime_type = part.get("mimeType", "")
            if mime_type == "text/plain":
                body = decode_base64_data(part.get("body", {}).get("data", ""))
                break
            if mime_type == "text/html" and not body:
                html = decode_base64_data(part.get("body", {}).get("data", ""))
                body = re.sub("<[^<]+?>", "", html)

    if not body:
        body = msg.get("snippet", "")

    return subject, body

def enable_watch():
    service = get_gmail_service()
    topic = os.getenv("PUBSUB_TOPIC")  # Uses .env—NO HARDCODE
    print("DEBUG: Loaded PUBSUB_TOPIC from .env:", topic)  # Confirm load
    if not topic:
        print("⚠️ PUBSUB_TOPIC not set in .env—skipping watch (use manual 'Fetch Emails' in UI)")
        return  # Exit—no error

    request_body = {
        "topicName": topic,
        "labelIds": ["INBOX"],
        "labelFilterAction": "include"
    }

    response = service.users().watch(
        userId="me",
        body=request_body
    ).execute()

    print("🔔 Gmail push notifications active for:", topic)
    print("Watch Response:", response)
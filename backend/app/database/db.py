import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool  # New: For larger pool

DB_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "emails.db")
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_FILE}"

# Engine with larger pool for real-time floods
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=QueuePool,  # Explicit pool
    pool_size=20,  # Increased: 20 connections
    max_overflow=30,  # Increased: 30 overflow
    pool_timeout=60,  # Increased: 60s timeout
    pool_pre_ping=True  # Ping before use (SQLite)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class EmailRecord(Base):
    __tablename__ = "emails"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(256), index=True, unique=False, nullable=True)
    subject = Column(String(1024), nullable=True)
    body = Column(Text, nullable=True)
    combined_text = Column(Text, nullable=True)
    cleaned_text = Column(Text, nullable=True)
    predicted_label = Column(String(128), nullable=True)
    confidence = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def save_email_record(session, message_id, subject, body, combined_text, cleaned_text, label, confidence):
    rec = EmailRecord(
        message_id=message_id,
        subject=subject,
        body=body,
        combined_text=combined_text,
        cleaned_text=cleaned_text,
        predicted_label=label,
        confidence=confidence
    )
    session.add(rec)
    session.commit()
    session.refresh(rec)
    return rec
# app/models/chat.py
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey('chat_sessions.id'), index=True)
    role = Column(String(20))  # system, user, assistant
    content = Column(LONGTEXT)
    context = Column(LONGTEXT, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
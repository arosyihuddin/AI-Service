from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.mysql import LONGTEXT, JSON
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
from datetime import datetime

def generate_uuid():
    return str(uuid.uuid4())

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_name = Column(String(100))
    user_id = Column(Integer(), ForeignKey("users.id"), index=True)
    material_ids = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey('chat_sessions.id'), index=True)
    role = Column(String(20))  # system, user, assistant
    content = Column(LONGTEXT)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

class Users(Base):
    __tablename__ = "users"
    
    id = Column(Integer(), primary_key=True)
    user_name= Column(String(100))
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
# app/services/chat_service.py
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.utils.logging import log
from together import Together
from app.models.chat import ChatSession, ChatMessage
from app.services.llm_service import llm
import uuid
from app.services.document_service import DocumentService
from app.schemas.document import DocumentSearchRequest
from app.utils.rules import PROMPT_CHAT_SYSTEM


class ChatService:
    def __init__(self):
        self.client = Together(api_key=settings.together_api_key)
        self.MAX_HISTORY = 2
        self.system_message_content = PROMPT_CHAT_SYSTEM
    
    async def process_chat(self, db: Session, user_input: str, material_ids: list[int], session_id: Optional[str] = None):
        try:
            # Validasi atau generate session ID
            if session_id and not self._validate_session(db, session_id):
                raise ValueError("Session ID tidak valid")
                
            session_id = session_id or self._create_new_session(db)
            
            
            # Retrieval material
            req = DocumentSearchRequest(material_ids=material_ids, query=user_input, k=settings.k_chat)
            context = await DocumentService.search_document_context(req)
            
            # Simpan pesan user
            self._save_message(db, session_id, "user", user_input)
            
            # Dapatkan history
            messages = self._get_messages(db, session_id)
            # print(messages)
            
            # Merge Message With Context
            new_user_input = self._merge_messages_context(user_input, context)
            
            merge_history_user_input = messages.copy()
            merge_history_user_input.append({"role": "user", "content": new_user_input})
            
            # Generate response AI
            ai_response = await self._generate_ai_response(merge_history_user_input)
            
            # Simpan response AI
            self._save_message(db, session_id, "assistant", ai_response)
            
            # Bersihkan history jika perlu
            self._trim_history(db, session_id)
            
            return ai_response, session_id
            
        except Exception as e:
            db.rollback()
            log.error(f"Chat error: {str(e)}")
            raise

    def get_session_history(self, db: Session, session_id: str) -> List[Dict]:
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id, ChatMessage.role != "system"
        ).order_by(ChatMessage.created_at.asc()).all()
        
        return [{
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at
        } for msg in messages]
    
    async def delete_session(self, db: Session, session_id: str):
        # Validasi session ID
        if session_id and not self._validate_session(db, session_id):
            raise ValueError("Session ID tidak valid")
        
        db.query(ChatMessage).filter_by(session_id=session_id).delete()
        db.query(ChatSession).filter_by(id=session_id).delete()
        db.commit()

    def _validate_session(self, db: Session, session_id: str) -> bool:
        return db.query(ChatSession).filter_by(id=session_id).first() is not None

    def _create_new_session(self, db: Session) -> str:
        new_session = ChatSession(id=str(uuid.uuid4()))
        db.add(new_session)
        db.commit()
        
        # Tambahkan pesan sistem
        self._save_message(db, new_session.id, "system", self.system_message_content, self.system_message_content)
        return new_session.id

    def _save_message(self, db: Session, session_id: str, role: str, content: str, context: str = None):
        new_message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            context=context
        )
        db.add(new_message)
        db.commit()
        db.refresh(new_message)

    def _get_messages(self, db: Session, session_id: str) -> List[Dict]:
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        return [{
            "role": msg.role,
            "content": msg.content
        } for msg in messages]

    def _trim_history(self, db: Session, session_id: str):
        # Hitung total messages
        total_messages = db.query(ChatMessage).filter_by(session_id=session_id).count()
        
        if total_messages > self.MAX_HISTORY * 2 + 1:
            # Dapatkan ID message tertua yang perlu dipertahankan
            keep_messages = db.query(ChatMessage.id).filter_by(session_id=session_id)\
                .order_by(ChatMessage.created_at.desc())\
                .limit(self.MAX_HISTORY * 2 + 1)\
                .subquery()
                
            # Hapus message yang lebih lama
            db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id,
                ~ChatMessage.id.in_(keep_messages)
            ).delete(synchronize_session=False)
            
            db.commit()

    async def _generate_ai_response(self, messages: List[Dict]) -> str:
        try:
            response = llm(messages, settings.llm_model)
            return response
        
        except Exception as e:
            log.error(f"LLM Error: {str(e)}")
            raise RuntimeError("Gagal menghasilkan respons dari AI")
    
    def _merge_messages_context(self, messages: str, context: str) -> str:
        return f"Question: {messages}\nMaterial Context: {context}"
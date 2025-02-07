# app/services/chat_service.py
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.config import settings
from app.utils.logging import log
from together import Together
from app.models.chat import ChatSession, ChatMessage, Users
from app.services.llm_service import llm
import uuid
from app.services.document_service import DocumentService
from app.schemas.document import DocumentSearchRequest
from app.utils.rules import prompt_chat_system, promt_classification_system
from datetime import datetime

class ChatService:
    def __init__(self):
        self.client = Together(api_key=settings.together_api_key)
        self.MAX_HISTORY = settings.max_history
    
    async def process_chat(self, db: Session, user_input: str, user_id: int, user_name: str, is_different: bool, material_ids: list[int] = None, session_id: Optional[str] = None):
        try:
            # Validasi atau generate session ID
            if session_id and not await self._validate_session(db, session_id):
                raise ValueError("Session ID tidak valid")
            session_name = ''    
            if not session_id:
                prompt_system = prompt_chat_system(user_name)
                session_id, session_name = session_id or await self._create_new_session(user_input, user_id, user_name, prompt_system, material_ids, db)
            else:
                session_name = await self._get_session_name(db, session_id)
            
            # Simpan pesan user
            await self._save_message(db, session_id, "user", user_input)
            
            # Update Material IDS
            if is_different:
                await self._update_material_ids(db, session_id, material_ids)
                
            # Dapatkan history
            messages = await self._get_messages(db, session_id)
            
            if material_ids is not None and len(material_ids) > 0:
                # Retrieval material
                req = DocumentSearchRequest(material_ids=material_ids, query=user_input, k=settings.k_chat)
                context = await DocumentService.search_document_context(req)
                log.warn(f"Context: {context[:100]}...")

                # Merge Message With Context
                user_input = self._merge_messages_context(user_input, context)
                
            log.warn(f"User input: {user_input[:200]}...")
            merge_history_user_input = messages.copy()
            merge_history_user_input.append({"role": "user", "content": user_input})
            
            # Generate response AI
            ai_response = await self._generate_ai_response(merge_history_user_input)
            await self._save_message(db, session_id, "assistant", ai_response)
            
            # Bersihkan history jika perlu
            await self._trim_history(db, session_id)
            return ai_response, session_id, session_name
            
        except Exception as e:
            db.rollback()
            log.error(f"Chat error: {str(e)}")
            raise

    async def get_chat_history(self, db: Session, session_id: str) -> List[Dict]:
        if session_id == '' and not self._validate_session(db, session_id):
            raise ValueError("Session ID tidak valid")
        
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id, 
            ChatMessage.role != "system"
        ).order_by(ChatMessage.created_at.asc()).all()
        
        return [{
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at
        } for msg in messages]
    
    async def get_session_history(self,db: Session,  user_id: int) -> List[str]:
        sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id, ChatSession.deleted_at == None).order_by(ChatSession.created_at.desc()).all()
        
        return [ session for session in sessions]
    async def delete_session(self, db: Session, session_id: str):
        # Validasi session ID
        if session_id and not await self._validate_session(db, session_id):
            raise ValueError("Session ID tidak valid")
        
        db.query(ChatMessage).filter_by(session_id=session_id).update({"deleted_at": datetime.now()})
        db.query(ChatSession).filter_by(id=session_id).first().soft_delete()
        db.commit()

    async def _validate_session(self, db: Session, session_id: str) -> bool:
        return db.query(ChatSession).filter_by(id=session_id, deleted_at=None).first() is not None
    
    async def _validate_user(self, db: Session, user_id: int) -> bool:
        return db.query(Users).filter_by(id=user_id).first() is not None

    async def _create_new_session(self, session_name: str, user_id: int, user_name: str, promt_system: str, material_ids: list[int], db: Session) -> str:
        if not await self._validate_user(db, user_id):
            db.add(Users(id=user_id, user_name=user_name))
            db.commit()
        new_session_name = ' '.join(i for i in session_name.split()[:3])
        new_session = ChatSession(id=str(uuid.uuid4()), user_id=user_id, session_name=new_session_name, material_ids=material_ids)
        db.add(new_session)
        db.commit()
        
        # Tambahkan pesan sistem
        await self._save_message(db, new_session.id, "system", promt_system)
        return new_session.id, new_session_name

    async def _save_message(self, db: Session, session_id: str, role: str, content: str):
        new_message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content
        )
        db.add(new_message)
        db.commit()
        db.refresh(new_message)

    async def _get_messages(self, db: Session, session_id: str) -> List[Dict]:
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id,
            ChatMessage.deleted_at == None
        ).order_by(ChatMessage.created_at.asc()).all()
        
        return [{
            "role": msg.role,
            "content": msg.content
        } for msg in messages]
    
    async def _get_session_name(self, db: Session, session_id: str) -> str:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise ValueError("Invalid session ID")
        return session.session_name
    
    async def _update_material_ids(self, db: Session, session_id: str, material_ids: list[int]):
        db.query(ChatSession).filter(ChatSession.id == session_id).update({"material_ids": material_ids})
        db.commit()

    async def _trim_history(self, db: Session, session_id: str):
        # Hitung total messages
        total_messages = db.query(ChatMessage).filter_by(session_id=session_id).count()
        
        if total_messages > self.MAX_HISTORY * 2 + 1:
            # Dapatkan ID message tertua yang perlu dipertahankan
            keep_messages = db.query(ChatMessage.id).filter_by(
                session_id=session_id,
                role = "system")\
                .order_by(ChatMessage.created_at.desc())\
                .limit(self.MAX_HISTORY * 2 + 1)\
                .subquery()
                
            keep_messages_select = select(keep_messages.c.id)
            
            # Hapus message yang lebih lama
            db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id,
                ~ChatMessage.id.in_(keep_messages_select)
            ).update({"deleted_at": datetime.now()}, synchronize_session=False)
            # ).delete(synchronize_session=False)
            
            db.commit()

    async def _generate_ai_response(self, messages: List[Dict]) -> str:
        try:
            response = llm(messages, settings.llm_model)
            return response
        
        except Exception as e:
            log.error(f"LLM Error: {str(e)}")
            raise RuntimeError("Gagal menghasilkan respons dari AI")
    
    # async def _get_materials(self, db: Session, material_ids: list[int]) -> List[Document]:
    #     return db.query(ChatSession).filter(Document.id.in_(material_ids)).all()
    
    def _merge_messages_context(self, messages: str, context: str) -> str:
        return f"Jawab pertanyaan ini : {messages}\nGunakan hanya context di bawah ini:\n{context}"
    
    
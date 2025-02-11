from typing import List, Dict, Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.core.config import settings
from app.utils.logging import log
from together import Together
from app.models.chat import ChatSession, ChatMessage, Users
from app.services.llm_service import llm_chat
import uuid
from app.services.document_service import DocumentService
from app.schemas.document import DocumentSearchRequest
from app.utils.rules import prompt_chat_system
from datetime import datetime
import json

class ChatService:
    def __init__(self):
        self.client = Together(api_key=settings.together_api_key)
        self.MAX_HISTORY = settings.max_history
    
    async def process_chat(self, db: AsyncSession, user_input: str, user_id: int, user_name: str, is_different: bool, material_ids: list[int] = None, session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        try:
            # Validasi atau generate session ID
            if session_id and not await self._validate_session(db, session_id):
                raise ValueError("Session ID tidak valid")
            
            session_name = ''    
            if not session_id:
                prompt_system = prompt_chat_system(user_name)
                session_id, session_name = await self._create_new_session(
                    user_input=user_input, 
                    user_id=user_id, 
                    user_name=user_name, 
                    promt_system=prompt_system, 
                    material_ids=material_ids, 
                    db=db)
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
            messages_for_llm = messages.copy()
            messages_for_llm.append({"role": "user", "content": user_input})
            
            # Generate response AI secara streaming
            full_response = ""
            async for chunk in self._generate_ai_response(messages_for_llm):
                full_response += chunk
                yield chunk
            
            # Simpan pesan asisten
            await self._save_message(db, session_id, "assistant", full_response)
            
            # Bersihkan history jika perlu
            await self._trim_history(db, session_id)
            
            yield f'\n[END_OF_STREAM]:{json.dumps({"status": "success", "session_id": session_id, "session_name": session_name})}'
        except Exception as e:
            await db.rollback()
            log.error(f"Chat error: {str(e)}")
            raise

    async def get_chat_history(self, db: AsyncSession, session_id: str) -> List[Dict]:
        if session_id == '' and not await self._validate_session(db, session_id):
            raise ValueError("Session ID tidak valid")
        
        messages_result = await db.execute(
            select(ChatMessage).filter(
                ChatMessage.session_id == session_id,
                ChatMessage.role != "system"
                ).order_by(ChatMessage.created_at.asc())
            )
        
        messages = messages_result.scalars().all()
        
        return [{
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at
        } for msg in messages]
    
    async def get_session_history(self,db: AsyncSession,  user_id: int) -> List[str]:
        result = await db.execute(
            select(ChatSession)
            .where(
                ChatSession.user_id == user_id,
                ChatSession.deleted_at == None
            )
            .order_by(ChatSession.created_at.desc())
        )
        sessions = result.scalars().all()
        return [ session for session in sessions]
    
    async def delete_session(self, db: AsyncSession, session_id: str):
        # Validasi session ID
        if session_id and not await self._validate_session(db, session_id):
            raise ValueError("Session ID tidak valid")
        
        await db.execute(
            update(ChatMessage)
            .filter_by(session_id=session_id)
            .values(deleted_at=datetime.now())
            )
        await db.execute(
            update(ChatSession)
            .filter_by(id=session_id)
            .values(deleted_at=datetime.now())
            )
        await db.commit()

    async def _validate_session(self, db: AsyncSession, session_id: str) -> bool:
        result = await db.execute(select(ChatSession).filter_by(id=session_id, deleted_at=None))
        return result.scalars().first() is not None
    
    async def _validate_user(self, db: AsyncSession, user_id: int) -> bool:
        result = await db.execute(select(Users).filter_by(id=user_id))
        return result.scalars().first() is not None

    async def _create_new_session(self, user_input: str, user_id: int, user_name: str, promt_system: str, material_ids: list[int], db: AsyncSession) -> str:
        if not await self._validate_user(db, user_id):
            db.add(Users(id=user_id, user_name=user_name))
            await db.commit()
        new_session_name = ' '.join(i for i in user_input.split()[:3])
        new_session = ChatSession(
            id=str(uuid.uuid4()), 
            user_id=user_id, 
            session_name=new_session_name, 
            material_ids=material_ids)
        db.add(new_session)
        await db.commit()
        
        # Tambahkan pesan sistem
        await self._save_message(db, new_session.id, "system", promt_system)
        return new_session.id, new_session_name

    async def _save_message(self, db: AsyncSession, session_id: str, role: str, content: str):
        new_message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content
        )
        db.add(new_message)
        await db.commit()
        await db.refresh(new_message)

    async def _get_messages(self, db: AsyncSession, session_id: str) -> List[Dict]:
        result = await db.execute(
            select(ChatMessage).where(
                ChatMessage.session_id == session_id,
                ChatMessage.deleted_at == None
            ).order_by(ChatMessage.created_at.asc())
        )
        messages = result.scalars().all()
        return [{"role": msg.role, "content": msg.content} for msg in messages]
    
    async def _get_session_name(self, db: AsyncSession, session_id: str) -> str:
        result = await db.execute(select(ChatSession).filter(ChatSession.id == session_id))
        session = result.scalars().first()
        if not session:
            raise ValueError("Invalid session ID")
        return session.session_name
    
    async def _update_material_ids(self, db: AsyncSession, session_id: str, material_ids: list[int]):
        getSession = await db.execute(select(ChatSession).filter(ChatSession.id == session_id))
        getSession.scalars().first().material_ids = material_ids
        await db.commit()

    async def _trim_history(self, db: AsyncSession, session_id: str):
        # Hitung total messages
        result = await db.execute(select(ChatMessage).filter_by(session_id=session_id, deleted_at=None))
        total_messages = len(result.scalars().all())
        
        if total_messages > self.MAX_HISTORY * 2 + 1:
            # Dapatkan ID message tertua yang perlu dipertahankan
            keep_messages_result = await db.execute(
                select(ChatMessage.id).where(
                    ChatMessage.session_id == session_id, 
                    ChatMessage.deleted_at == None,
                    )
                .order_by(ChatMessage.created_at.desc())
                .limit(self.MAX_HISTORY * 2)
                )
            
            keep_messages = keep_messages_result.scalars().all()
            
            # Hapus message yang lebih lama
            result = await db.execute(
                update(ChatMessage).where(
                    ChatMessage.session_id == session_id,
                    ChatMessage.role != "system",
                    ChatMessage.deleted_at == None,
                    ~ChatMessage.id.in_(keep_messages)
                    ).values(deleted_at=datetime.now())
            )
            await db.commit()

    async def _generate_ai_response(self, messages: List[Dict]) -> AsyncGenerator[str, None]:
        try:
            async for chuck in llm_chat(messages, settings.llm_model):
                yield chuck
        except Exception as e:
            log.error(f"LLM Error: {str(e)}")
            raise RuntimeError("Gagal menghasilkan respons dari AI")
    
    def _merge_messages_context(self, messages: str, context: str) -> str:
        return f"Jawab pertanyaan ini : {messages}\ncontext:\n{context}"
    
    
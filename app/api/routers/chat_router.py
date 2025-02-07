# app/routers/chat.py
from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()
chat_service = ChatService()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        response_text, session_id, session_name = await chat_service.process_chat(
            db=db,
            user_input=request.user_input,
            material_ids=request.material_ids,
            session_id=request.session_id,
            user_id=request.user_id,
            user_name=request.user_name,
            is_different=request.is_different
        )
        
        return ChatResponse(
            response=response_text,
            session_name=session_name,
            session_id=session_id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )

@router.delete("/chat/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    try:
        await chat_service.delete_session(db, session_id)
        return {"status": 200, "message": "Session deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/chat/history")
async def get_history(session_id: str, db: Session = Depends(get_db)):
    try:
        history = await chat_service.get_chat_history(db, session_id)
        return {"status": 200, "history": history}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/chat/sessions")
async def  get_sessions(user_id: int, db: Session = Depends(get_db)):
    try:
        sessions = await chat_service.get_session_history(db, user_id)
        return {"status": 200, "sessions": sessions}
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
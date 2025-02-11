from fastapi import APIRouter, HTTPException
from app.schemas.quiz import QuizGenerateRequest
from app.services.quiz_service import QuizService
from app.utils.logging import log

router = APIRouter()

@router.post("/generate")
async def generate_quiz(request: QuizGenerateRequest):
    try:
        return await QuizService.generate_quiz(request)
    except HTTPException as e:
        log.error(e.detail)
        raise e
    except Exception as e:
        log.error(f"Quiz generation error: {str(e)}")
        raise HTTPException(500, f"Quiz generation error: {str(e)}")
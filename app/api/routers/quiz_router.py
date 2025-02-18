from fastapi import APIRouter, HTTPException
from app.schemas.quiz import QuizGenerateRequest, AutoCorrectRequest
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


@router.post("/autocorrect")
async def auto_correct(request: AutoCorrectRequest):
    try:
        return await QuizService.auto_correct(request)
    except HTTPException as e:
        log.error(e.detail)
        raise e
    except Exception as e:
        log.error(f"Quiz generation error: {str(e)}")
        raise HTTPException(500, f"Quiz generation error: {str(e)}")

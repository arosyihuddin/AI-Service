# app/services/quiz_service.py
from app.schemas.quiz import QuizGenerateRequest
from app.utils.rules import multiple_rules, descriptive_rules
from app.utils.logging import log
from fastapi import HTTPException
from app.db.database_vector import get_db_vector
from app.services.llm_service import llm
import requests
from app.core.config import settings
from app.services.document_service import DocumentService
from app.schemas.document import DocumentSearchRequest
import json

QUESTION_RULES = {
    "multiple": multiple_rules,
    "descriptive": descriptive_rules
}

class QuizService:
    @staticmethod
    async def generate_quiz(request: QuizGenerateRequest):
        """Handle the logic to generate a quiz"""
        db = get_db_vector() 
        if db is None:
            raise HTTPException(500, "Database not initialized")
        
        # Mencari materi yang relevan dengan kata kunci
        question = f"carikan materi yang berkaitan dengan {request.topics}"
        req = DocumentSearchRequest(material_ids=request.material_ids, topics=question, k=settings.k_quiz)
        context = await DocumentService.get_material_context(req)
        log.info(f"Conentext: {context[:50]}...")
        if context == '':
            raise HTTPException(404, f"Gagal Mencari Materi dengan topik {request.topics} Gunakan topik lain")
        
        question_with_context = f"question: buatkan {request.total_soal} soal dengan quiz id nya {request.quiz_id}, topik yang ingin dibuat adalah {request.topics}, terkait dengan materi berikut. materi: {context}"
        
        # Menentukan fungsi aturan berdasarkan jenis soal
        rules_function = QUESTION_RULES.get(request.type_soal)
        if not rules_function:
            raise HTTPException(500, "Invalid Tipe Soal")
        
        rules = rules_function(question_with_context)
        
        # Mengirimkan permintaan ke LLM model untuk menghasilkan soal
        try:
            log.info(f"Use Model: {settings.llm_model}")
            response_model = llm(rules, settings.llm_model)
            headers = {
                "x-api-key": settings.lms_x_api_key,
                "Content-Type": "application/json",
            }

            # Mengirimkan POST request ke endpoint dengan body JSON
            response = requests.post(settings.lms_url_api, data=response_model, headers=headers).json()
            
            # Memeriksa status respons
            if response.get("status") == 200:
                if request.show_quiz:
                    try:
                        quiz = json.loads(response_model)
                    except Exception as e:
                        log.error(f"Failed to parse JSON for Show Quiz: {str(e)}")
                        raise e
                    return {"success":True, "status":200, "message":"Success Generate Quiz", "quiz": quiz["questions"]}
                else:
                    return {"success":True, "status":200, "message":"Success Generate Quiz"}
            else:
                raise HTTPException(status_code=400, detail="Failed Save Quiz")
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=400, detail="Failed Generate Quiz")
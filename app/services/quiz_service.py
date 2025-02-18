from app.schemas.quiz import QuizGenerateRequest, AutoCorrectRequest
from app.utils.rules import multiple_rules, descriptive_rules, auto_correct_rules
from app.utils.logging import log
from fastapi import HTTPException
from app.db.database_vector import get_db_vector
from app.services.llm_service import llm, llm_autocorrect
from app.core.config import settings
from app.services.document_service import DocumentService
from app.schemas.document import DocumentSearchRequest
import httpx
import json
from concurrent.futures import ThreadPoolExecutor
import asyncio

# Buat executor global untuk parsing JSON
executor = ThreadPoolExecutor()

QUESTION_RULES = {"multiple": multiple_rules, "descriptive": descriptive_rules}


class QuizService:
    @staticmethod
    async def generate_quiz(request: QuizGenerateRequest):
        """Handle the logic to generate a quiz"""
        db = get_db_vector()
        if db is None:
            raise HTTPException(500, "Database not initialized")

        # Mencari materi yang relevan dengan kata kunci
        question = f"carikan materi yang berkaitan dengan {request.topics}"
        req = DocumentSearchRequest(
            material_ids=request.material_ids, topics=question, k=settings.k_quiz
        )
        context = await DocumentService.get_material_context(req)
        log.warn(f"Context: {context[:50]}...")
        if context == "":
            raise HTTPException(
                404,
                f"Gagal Mencari Materi dengan topik {request.topics} Gunakan topik lain",
            )

        question_with_context = f"question: buatkan {request.total_soal} soal dengan quiz id nya {request.quiz_id}, topik yang ingin dibuat adalah {request.topics}, terkait dengan materi berikut. materi: {context}"

        # Menentukan fungsi aturan berdasarkan jenis soal
        rules_function = QUESTION_RULES.get(request.type_soal)
        if not rules_function:
            raise HTTPException(500, "Invalid Tipe Soal")

        rules = rules_function(question_with_context)

        # Mengirimkan permintaan ke LLM model untuk menghasilkan soal
        try:
            log.warn(f"Use Model: {settings.quiz_model}")
            response_model = await llm(rules, settings.quiz_model)

            # Mengirimkan POST request ke endpoint dengan body JSON
            response = await QuizService._save_quiz(response_model)

            # Memeriksa status respons
            if response.get("status") == 200:
                if request.show_quiz:
                    try:
                        quiz = await QuizService._parse_json_async(response_model)
                    except Exception as e:
                        log.error(f"Failed to parse JSON for Show Quiz: {str(e)}")
                        raise e
                    return {
                        "success": True,
                        "status": 200,
                        "message": "Success Generate Quiz",
                        "quiz": quiz["questions"],
                    }
                else:
                    return {
                        "success": True,
                        "status": 200,
                        "message": "Success Generate Quiz",
                    }
            else:
                log.error(f"Failed to save quiz: {response}")
                raise HTTPException(status_code=400, detail="Failed Save Quiz")
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=400, detail="Failed Generate Quiz")

    async def _save_quiz(data):
        headers = {
            "x-api-key": settings.lms_x_api_key,
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.lms_url_api + "/generate", data=data, headers=headers
            )
            return response.json()

    async def _parse_json_async(json_string):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, lambda: json.loads(json_string))

    async def auto_correct(request: AutoCorrectRequest):
        db = get_db_vector()
        if db is None:
            raise HTTPException(500, "Database not initialized")

        dedscriptive = []
        multiple = []

        for i in request.answers:
            if i["correct_answer"] != None:
                dedscriptive.append(
                    {
                        "question_id": i["question_id"],
                        "correct_answer": i["correct_answer"],
                        "answer": i["user_answer"],
                        "max_grade": i["max_grade"],
                        "status": i["status"],
                    }
                )
            else:
                multiple.append(
                    {
                        "question_id": i["question_id"],
                        "answer": i["user_answer"],
                        "grade": i["max_grade"],
                        "status": i["status"],
                    }
                )
        try:
            query = f"Quiz Result ID: {request.quiz_result_id}, Jawaban: {dedscriptive}"
            query_rules = auto_correct_rules(query)
            result = await llm_autocorrect(query_rules, settings.autocorrect_model)
            result_parse = json.loads(result)

            if len(multiple) > 0:
                for i in multiple:
                    result_parse["results"].append(i)

            return {
                "success": True,
                "status": 200,
                "data": result_parse,
            }
        except Exception as e:
            log.error(f"Failed process auto correct: {str(e)}")
            raise HTTPException(status_code=400, detail="Failed Process Auto Correct")

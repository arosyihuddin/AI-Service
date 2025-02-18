from pydantic import BaseModel
from typing import List, Optional


# Request schema for generating a quiz
class QuizGenerateRequest(BaseModel):
    type_soal: str
    total_soal: int = 5
    material_ids: List[int]
    quiz_id: int
    topics: str
    show_quiz: Optional[bool] = False


class AutoCorrectRequest(BaseModel):
    quiz_result_id: int
    answers: List[dict]

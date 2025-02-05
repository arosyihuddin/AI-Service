from pydantic import BaseModel
from typing import List

# Request schema for generating a quiz
class QuizGenerateRequest(BaseModel):
    type_soal: str
    total_soal: int = 5
    material_ids: List[int]
    quiz_id: int
    keywords: str
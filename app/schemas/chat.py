from pydantic import BaseModel
from typing import Optional, List

class ChatRequest(BaseModel):
    user_input: str
    session_id: Optional[str] = None  # Opsional untuk new session
    material_ids: List[int]

class ChatResponse(BaseModel):
    response: str
    session_id: str
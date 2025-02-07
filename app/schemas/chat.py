from pydantic import BaseModel
from typing import Optional, List

class ChatRequest(BaseModel):
    user_input: str
    session_id: Optional[str] = None  # Opsional untuk new session
    material_ids: Optional[List[int]] = None
    user_name: str
    user_id: int
    is_different: bool

class ChatResponse(BaseModel):
    response: str
    session_id: str
    session_name: str
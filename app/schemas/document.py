from pydantic import BaseModel
from typing import List, Optional

# Request schema for creating a document
class DocumentCreateRequest(BaseModel):
    material_id: int
    source: str
    course_name: str
    module: str
    description: str

# Request schema for updating a document
class DocumentUpdateRequest(BaseModel):
    material_id: int
    source: str
    course_name: str
    module: str
    description: str

# Request schema for deleting a document
class DocumentDeleteRequest(BaseModel):
    material_id: int

class DocumentSearchRequest(BaseModel):
    material_ids: Optional[List[int]] = None
    query: Optional[str] = None
    keywords: Optional[str] = None
    k: int

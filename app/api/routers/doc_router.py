# app/api/routers/doc_router.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.schemas.document import (
    DocumentCreateRequest,
    DocumentUpdateRequest,
    DocumentDeleteRequest,
    DocumentSearchRequest
)
from app.services.document_service import DocumentService
from app.utils.logging import log

router = APIRouter()

# ==================== GET ====================
@router.get("/")
async def get_all_document():
    try:
        return await DocumentService.get_document()
    except Exception as e:
        log.error(f"Document fetch error: {str(e)}")
        raise HTTPException(500, "Gagal mengambil dokumen. Error: " + str(e))

@router.get("/{material_id}")
async def get_document(material_id: int):
    try:
        return await DocumentService.get_document(material_id)
    except Exception as e:
        log.error(f"Document fetch error: {str(e)}")
        raise HTTPException(500, "Gagal mengambil dokumen. Error: " + str(e))

# ==================== POST ====================
@router.post("/search")
async def search_document(request: DocumentSearchRequest):
    try:
        result = await DocumentService.search_document(request)
        return {"success": True, "status": 200, "data": result}
    except Exception as e:
        log.error(f"Document search error: {str(e)}")
        raise HTTPException(500, "Gagal mencari dokumen. Error: " + str(e))
    
@router.post("/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    material_id: int = Form(...),
    source: str = Form(...),       
    course_name: str = Form(...),       
    module: str = Form(...),
    description: str = Form(...),
):
    """Upload dokumen materi baru"""
    try:
        request = DocumentCreateRequest(material_id=material_id, source=source, course_name=course_name, module=module, description=description)
        return await DocumentService.upload_document(file, request)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        log.error(f"Upload error: {str(e)}")
        raise HTTPException(500, "Gagal mengupload dokumen")

# ==================== PUT ====================
@router.put("/update")
async def update_document(
    file: UploadFile = File(...),
    material_id: int = Form(...),
    source: str = Form(...),
    course_name: str = Form(...),
    module: str = Form(...),
    description: str = Form(...),
):
    """Update dokumen existing"""
    try:
        request = DocumentUpdateRequest(material_id=material_id, source=source, course_name=course_name, module=module, description=description)
        return await DocumentService.update_document(file, request)
    except Exception as e:
        log.error(f"Update error: {str(e)}")
        raise HTTPException(500, "Gagal update dokumen")

# ==================== DELETE ====================
@router.delete("/delete")
async def delete_document(request: DocumentDeleteRequest):
    """Hapus dokumen dari sistem"""
    try:
        return await DocumentService.delete_document(request)
    except Exception as e:
        log.error(f"Delete error: {str(e)}")
        raise HTTPException(500, "Gagal menghapus dokumen")
# app/services/document_service.py
from fastapi import UploadFile, HTTPException
from app.db.database_vector import deleteDocHandler, insert, get_db
from app.schemas.document import DocumentCreateRequest, DocumentDeleteRequest, DocumentUpdateRequest, DocumentSearchRequest
from app.utils.file_handler import PDFHandler
from app.utils.logging import log

class DocumentService:
    @staticmethod
    async def upload_document(file: UploadFile, request: DocumentCreateRequest):
        """Handle the business logic for uploading a document"""
        try:
            # Validate the file format (must be a PDF)
            await PDFHandler.validate_file(file)
            
            # Save the file temporarily
            temp_path = await PDFHandler.save_temp_file(file)
            
            # Insert document data into the FAISS database
            await insert(temp_path, request.material_id, request.source, request.course_name, request.module, request.description)
            
            # Cleanup temporary file
            PDFHandler.cleanup_temp_file(temp_path)
            
            return {"status": "success", "message": "Document successfully uploaded"}
        
        except ValueError as e:
            log.error(f"File validation failed: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            log.error(f"Error during document upload: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to upload document")

    @staticmethod
    async def update_document(file: UploadFile, request: DocumentUpdateRequest):
        """Handle updating an existing document"""
        try:
            # Validate and process file as in upload_document method
            await PDFHandler.validate_file(file)
            temp_path = await PDFHandler.save_temp_file(file)
            
            # Delete existing document data first
            await deleteDocHandler(request.material_id)
            
            # Add the updated document to the database
            await insert(temp_path, request.material_id, request.source, request.course_name, request.module, request.description)
            
            PDFHandler.cleanup_temp_file(temp_path)
            
            return {"status": "success", "message": "Document successfully updated"}
        
        except Exception as e:
            log.error(f"Error during document update: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update document")
    
    @staticmethod
    async def delete_document(request: DocumentDeleteRequest):
        """Handle deleting a document from the system"""
        try:
            # Delete the document from the FAISS database
            result = await deleteDocHandler(request.material_id)
            
            if result['success']:
                return {"status": "success", "message": "Document successfully deleted"}
            else:
                raise HTTPException(status_code=400, detail=result['message'])
        
        except Exception as e:
            log.error(f"Error during document deletion: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete document")

    @staticmethod
    async def get_document(material_id: int = None):
        db = get_db()  # Ambil instance terbaru
        if db is None:
            raise HTTPException(500, "Database not initialized")
        try:
            # Jika material_id tidak diberikan, tampilkan semua data
            if material_id is None:
                docs = [
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata
                    }
                    for doc in db.docstore._dict.values()
                ]
                return {"success": True, "status": 200, "data": docs}
            
            # Jika material_id diberikan, filter berdasarkan parent_id
            docs = []
            for _, doc in db.docstore._dict.items():
                # if doc.metadata.get("parent_id") == int(material_id):
                if doc.metadata.get("parent_id") == material_id:
                    docs.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata
                    })
            return {"success": True, "status": 200, "data": docs}
        
        except Exception as e:
            raise HTTPException(500, f"Gagal mengambil dokumen: {str(e)}")

    @staticmethod
    async def search_document(request: DocumentSearchRequest):
        db = get_db()
        if db is None:
            raise HTTPException(500, "Database not initialized")
        try:
            query = ''
            if request.topics is not None:
                query = f"carikan semua materi yang berkaitan dengan {request.topics}"
            else:
                query  = request.query
            isFilter = {"parent_id": {"$in": request.material_ids}} if request.material_ids is not None else None
            result = db.similarity_search(query, k=request.k, filter=isFilter)
            sorted_result = sorted(result, key=lambda x: x.metadata["chunk_id"])
            return sorted_result
        except Exception as e:
            raise HTTPException(500, f"Gagal mencari dokumen: {str(e)}")
        
    @staticmethod
    async def search_document_context(request: DocumentSearchRequest):
        db = get_db()
        if db is None:
            raise HTTPException(500, "Database not initialized")
        try:
            result = await DocumentService.search_document(request)
            context = "".join([f'-[SOURCE: {doc.metadata["course_name"]}, Modul: {doc.metadata["module"]}, Halaman: {doc.metadata["page"]}, Link: {doc.metadata["source"]}]\n{doc.page_content}\n' for doc in result])
            return context.strip()
        except Exception as e:
            raise HTTPException(500, f"Gagal mencari dokumen context: {str(e)}")
    
    @staticmethod
    async def get_material_context(request: DocumentSearchRequest):
        db = get_db()
        if db is None:
            raise HTTPException(500, "Database not initialized")
        try:
            result = await DocumentService.search_document(request)
            context = "".join([chunk.page_content for chunk in result])
            return context.strip()
        except Exception as e:
            raise HTTPException(500, f"Gagal mencari dokumen context: {str(e)}")
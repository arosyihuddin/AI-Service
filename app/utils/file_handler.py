# app/utils/file_handler.py
from fastapi import UploadFile
import shutil
import os

class PDFHandler:

    @staticmethod
    async def validate_file(file: UploadFile):
        """Validate if the file is a PDF"""
        if not file.filename.endswith('.pdf'):
            raise ValueError("File must be a PDF")

    @staticmethod
    async def save_temp_file(file: UploadFile) -> str:
        """Save the uploaded file temporarily"""
        temp_file_path = f"temp/{file.filename}"
        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return temp_file_path

    @staticmethod
    def cleanup_temp_file(temp_path: str):
        """Cleanup the temporary file after processing"""
        if os.path.exists(temp_path):
            os.remove(temp_path)

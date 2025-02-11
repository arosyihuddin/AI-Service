from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores.faiss import FAISS
from app.services.llm_service import embeddings
from contextlib import asynccontextmanager
from langchain.schema import Document
from app.utils.logging import log
from uuid import uuid4
import os
import asyncio
import re
from app.core.config import settings
from app.core.database import async_session_maker
from concurrent.futures import ThreadPoolExecutor
import asyncio
from sqlalchemy import text

_db_instance = None  
folder_path = os.path.join(os.getcwd(), "app/db", settings.db_vector_path)

def get_db_vector():
    if _db_instance is None:
        raise RuntimeError("FAISS database has not been initialized.")
    return _db_instance

# Define the text splitter for chunking large text documents
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=int(settings.chunk_size),  # Size of each chunk in characters
    chunk_overlap=int(settings.chunk_overlap),  # Number of overlapping characters between chunks
    strip_whitespace=True,
    separators=["\n\n", "\n", " ", ""],  # Prioritize natural breaks like paragraph breaks
)

executor = ThreadPoolExecutor()

@asynccontextmanager
async def init_db(app):
    global _db_instance
    log.info("Initializing databases...")
    
    # Step 1: Load FAISS vector database asynchronously
    try:
        log.info("Loading FAISS vector database...")
        loop = asyncio.get_event_loop()
        _db_instance = await loop.run_in_executor(
            executor,
            lambda: FAISS.load_local(
                folder_path=folder_path,
                embeddings=embeddings,
                allow_dangerous_deserialization=True
            )
        )
        log.info("FAISS vector database loaded successfully.")
        
    except Exception as e:
        log.error(f"Failed to load FAISS vector database: {str(e)}")
        raise RuntimeError("Failed to initialize FAISS database.") from e
    
    # Step 2: Test MySQL database connection
    try:
        log.info("Connecting to MySQL database...")
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        log.info("MySQL database connected successfully.")
    except Exception as e:
        log.error(f"Failed to connect to MySQL database: {str(e)}")
        raise RuntimeError("Failed to connect to MySQL database.") from e

    yield  # Keep the application running

    ## Shutdown resources
    log.info("Shutting down databases.")
    executor.shutdown(wait=True)

async def insert(file_path: str, material_id: int, source: str, course_name: str, module:str, description: str):
    """Insert document data into FAISS database."""
    db = get_db_vector()
    
    if not db:
        raise Exception("Database has not been initialized")
    
    # Check if the material_id already exists in the database
    existing_ids = [
        doc.metadata["parent_id"] 
        for doc in db.docstore._dict.values()
        if doc.metadata.get("parent_id") == material_id
    ]
    if existing_ids:
        raise Exception(f"Material ID {material_id} already exists in the database")
    
    try:
        # Load PDF document
        loader = PyPDFLoader(file_path)
        pages = await asyncio.to_thread(loader.load)  # Load PDF in a separate thread to avoid blocking
        log.info(f"Found {len(pages)} pages in the document.")
        
        # Build documents by splitting content into chunks
        documents = []
        ids = []
        for page in pages:
            clean_content = re.sub(r'[\t\n]+', ' ', page.page_content)
            chunks = text_splitter.split_text(clean_content)
            for index, chunk in enumerate(chunks):
                # Generate a unique document ID
                doc_id = str(uuid4())
                
                # Define metadata for the document
                metadata = {
                    "parent_id": material_id,
                    "chunk_id": index,
                    "course_name": course_name,
                    "description": description,
                    "module": module,
                    "source": source,
                    "page": page.metadata.get("page", 0)+1,
                }
                
                # Add document to the list
                documents.append(Document(metadata=metadata, page_content=chunk))
                ids.append(doc_id)
        
        # Add documents to FAISS
        await asyncio.to_thread(db.add_documents, documents=documents, ids=ids)
        
        # Save the FAISS database
        await asyncio.to_thread(db.save_local, folder_path=folder_path)
        
        log.info(f"Successfully added {len(documents)} chunks to the database.")
        
    except Exception as e:
        log.error(f"Error processing PDF: {str(e)}")
        raise

async def deleteDocHandler(material_id: int):
    """Delete document(s) from the FAISS database using material_id."""
    db = get_db_vector()
    if not db:
        return {"success": False, "message": "Database not initialized"}
    
    try:
        # Find all document IDs with the specified material_id
        ids_to_delete = []
        for doc_id, doc in db.docstore._dict.items():
            if doc.metadata.get("parent_id") == material_id:
                ids_to_delete.append(doc_id)
        
        if not ids_to_delete:
            return {"success": False, "status": 400, "message": "No documents found for the given material_id"}
        
        # Delete documents from FAISS
        await asyncio.to_thread(db.delete, ids=ids_to_delete)
        
        # Save changes to the FAISS database
        await asyncio.to_thread(db.save_local, folder_path=folder_path)
        
        return {"success": True, "status": 200, "deleted_count": len(ids_to_delete)}
    
    except Exception as e:
        log.error(f"Error deleting documents: {str(e)}")
        return {"success": False, "status": 400, "message": str(e)}

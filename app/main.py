# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database_vector import init_db
from app.core.config import settings
from app.api.routers import doc_router, quiz_router, system_router, chat_router

app = FastAPI(
    title="AI Service",
    description="API untuk integrasi dengan AI, AI dapat menjadi pengalaman yang bagus untuk pengguna serta mempermudah pengguna dalam menjalankan aplikasi",
    version="1.0.0",
    lifespan=init_db
)

# Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Include all routers
app.include_router(chat_router.router, prefix="/api/v1", tags=["Chatbot"])
app.include_router(doc_router.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(quiz_router.router, prefix="/api/v1/quiz", tags=["Quiz"])
app.include_router(system_router.router, prefix="/api/v1/system", tags=["System Monitoring"])


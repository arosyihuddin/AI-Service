from pydantic_settings import BaseSettings
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv(override=True)


class Settings(BaseSettings):
    CORS_ORIGINS: List[str] = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]

    # System Settings
    log_level: str = "INFO"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    quiz_model: str = "llama"
    chat_model: str = "openai"

    # MODEL API Settings
    together_api_key: str
    openai_api_key: str
    openrouter_api_key: str
    openrouter_baseurl: str

    # LMS Settings
    lms_url_api: str
    lms_x_api_key: str

    # Database Settings
    db_vector_path: Optional[str] = "main_db"
    db_host: str
    db_user: str
    db_password: str
    db_name: str

    k_quiz: int
    k_chat: int

    max_history: int

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # Allow extra fields that are not defined in the model


# Global instance of settings
settings = Settings()

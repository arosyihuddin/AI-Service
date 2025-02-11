from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings

SQLALCHEMY_DATABASE_URL = f"mysql+asyncmy://{settings.db_user}:{settings.db_password}@{settings.db_host}/{settings.db_name}"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
)

Base = declarative_base()
        
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
async def get_db():
    async with async_session_maker() as session:
        yield session
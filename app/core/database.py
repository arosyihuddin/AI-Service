from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings

SQLALCHEMY_DATABASE_URL = f"mysql+asyncmy://{settings.db_user}:{settings.db_password}@{settings.db_host}/{settings.db_name}"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,  # Jumlah koneksi maksimum dalam pool
    max_overflow=10,  # Jumlah koneksi tambahan yang diizinkan
    pool_timeout=30,  # Waktu tunggu maksimum untuk mendapatkan koneksi
    pool_recycle=3600,  # Recycle koneksi setiap 1 jam
    echo_pool=True,
)

Base = declarative_base()

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    async with async_session_maker() as session:
        yield session

from logging.config import fileConfig
from app.core.database import Base
from app.models.chat import ChatSession, ChatMessage

from sqlalchemy.ext.asyncio import create_async_engine
import asyncio
from sqlalchemy import pool
from app.core.config import settings

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
def do_run_migrations(connection):
    """
    This function is called within a synchronous context (via run_sync).
    All Alembic operations (like inspection) will run here on a synchronous connection.
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()
        

async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""
    # Build the async database URL.
    SQLALCHEMY_DATABASE_URL = (
        f"mysql+asyncmy://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}/{settings.db_name}"
    )

    # Create an async engine.
    connectable = create_async_engine(SQLALCHEMY_DATABASE_URL, poolclass=pool.NullPool)

    # Connect asynchronously.
    async with connectable.connect() as connection:
        # Run the synchronous migration code within the async connection.
        await connection.run_sync(do_run_migrations)

    # Dispose the engine once done.
    await connectable.dispose()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
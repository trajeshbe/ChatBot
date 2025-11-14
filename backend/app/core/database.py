from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from app.core.config import settings
from app.models.database import Base
import logging

logger = logging.getLogger(__name__)

# Async engine for main operations
async_engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Sync engine for migrations and initial setup
sync_engine = create_engine(
    settings.SYNC_SQLALCHEMY_DATABASE_URI,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

# Async session maker
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """Dependency for getting async database sessions"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Don't auto-commit - let endpoints handle commits explicitly
            # This prevents double-commit issues and gives better control
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database with tables and pgvector extension"""
    import asyncio
    max_retries = 5
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            logger.info(f"Database initialization attempt {attempt + 1}/{max_retries}")

            # Create extension using sync engine
            with sync_engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                logger.info("pgvector extension created/verified")

            # Create all tables
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Database tables created/verified")

            # Create vector index for better performance
            async with async_engine.begin() as conn:
                await conn.execute(
                    text("""
                        CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
                        ON document_chunks USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 100);
                    """)
                )
                await conn.execute(
                    text("""
                        CREATE INDEX IF NOT EXISTS idx_query_cache_embedding
                        ON query_cache USING ivfflat (query_embedding vector_cosine_ops)
                        WITH (lists = 100);
                    """)
                )
                logger.info("Vector indexes created/verified")

            logger.info("Database initialization successful")
            return

        except Exception as e:
            logger.warning(f"Database initialization attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"Database initialization failed after {max_retries} attempts")
                raise


async def close_db():
    """Close database connections"""
    await async_engine.dispose()
    sync_engine.dispose()
    logger.info("Database connections closed")

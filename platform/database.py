"""Platform database — PostgreSQL connection for entity system."""
import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

DATABASE_URL = os.environ.get(
    "PLATFORM_DATABASE_URL",
    "postgresql+asyncpg://evolvixos:evolvixos@127.0.0.1:5432/evolvixos"
)

engine = create_async_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with async_session() as session:
        yield session

async def init_db():
    """Create platform tables."""
    async with engine.begin() as conn:
        await conn.execute(__import__('sqlalchemy').text("""
            CREATE TABLE IF NOT EXISTS platform_entities (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                schema JSONB NOT NULL,
                created_date TIMESTAMP DEFAULT NOW(),
                updated_date TIMESTAMP DEFAULT NOW(),
                created_by VARCHAR(255)
            )
        """))
        await conn.execute(__import__('sqlalchemy').text("""
            CREATE TABLE IF NOT EXISTS platform_functions (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                code TEXT NOT NULL,
                language VARCHAR(20) DEFAULT 'python',
                env_vars JSONB DEFAULT '{}',
                created_date TIMESTAMP DEFAULT NOW(),
                updated_date TIMESTAMP DEFAULT NOW(),
                created_by VARCHAR(255)
            )
        """))
        await conn.execute(__import__('sqlalchemy').text("""
            CREATE TABLE IF NOT EXISTS platform_workflows (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                definition JSONB NOT NULL,
                trigger_type VARCHAR(50) NOT NULL,
                trigger_config JSONB,
                status VARCHAR(20) DEFAULT 'active',
                created_date TIMESTAMP DEFAULT NOW(),
                updated_date TIMESTAMP DEFAULT NOW(),
                created_by VARCHAR(255)
            )
        """))
        await conn.execute(__import__('sqlalchemy').text("""
            CREATE TABLE IF NOT EXISTS platform_files (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                file_path TEXT NOT NULL,
                file_url TEXT,
                is_private BOOLEAN DEFAULT FALSE,
                content_type VARCHAR(100),
                file_size BIGINT,
                created_date TIMESTAMP DEFAULT NOW(),
                created_by VARCHAR(255)
            )
        """))
        print("Platform tables created")

"""Platform database — PostgreSQL connection for entity system."""
import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text

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
    """Create all platform tables."""
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS platform_entities (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                schema JSONB NOT NULL,
                rls_enabled BOOLEAN DEFAULT FALSE,
                created_date TIMESTAMP DEFAULT NOW(),
                updated_date TIMESTAMP DEFAULT NOW(),
                created_by VARCHAR(255)
            )
        """))
        await conn.execute(text("""
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
        await conn.execute(text("""
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
        await conn.execute(text("""
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
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS platform_apps (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                slug VARCHAR(200) UNIQUE NOT NULL,
                status VARCHAR(20) DEFAULT 'draft',
                is_public BOOLEAN DEFAULT FALSE,
                share_token VARCHAR(255),
                theme JSONB DEFAULT '{}',
                settings JSONB DEFAULT '{}',
                version INTEGER DEFAULT 1,
                created_date TIMESTAMP DEFAULT NOW(),
                updated_date TIMESTAMP DEFAULT NOW(),
                created_by VARCHAR(255)
            )
        """))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS platform_pages (
                id SERIAL PRIMARY KEY,
                app_id INTEGER REFERENCES platform_apps(id) ON DELETE CASCADE,
                name VARCHAR(200) NOT NULL,
                slug VARCHAR(200) NOT NULL,
                layout JSONB NOT NULL DEFAULT '[]',
                page_type VARCHAR(50) DEFAULT 'custom',
                is_home BOOLEAN DEFAULT FALSE,
                sort_order INTEGER DEFAULT 0,
                created_date TIMESTAMP DEFAULT NOW(),
                updated_date TIMESTAMP DEFAULT NOW(),
                created_by VARCHAR(255)
            )
        """))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS platform_connectors (
                id SERIAL PRIMARY KEY,
                provider VARCHAR(50) NOT NULL,
                name VARCHAR(200) NOT NULL,
                config JSONB DEFAULT '{}',
                status VARCHAR(20) DEFAULT 'disconnected',
                access_token TEXT,
                refresh_token TEXT,
                token_expires TIMESTAMP,
                scopes TEXT[],
                created_date TIMESTAMP DEFAULT NOW(),
                updated_date TIMESTAMP DEFAULT NOW(),
                created_by VARCHAR(255)
            )
        """))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS platform_versions (
                id SERIAL PRIMARY KEY,
                entity_type VARCHAR(50) NOT NULL,
                entity_id VARCHAR(255),
                entity_name VARCHAR(200),
                snapshot JSONB NOT NULL,
                change_description TEXT,
                version_number INTEGER,
                created_date TIMESTAMP DEFAULT NOW(),
                created_by VARCHAR(255)
            )
        """))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS platform_activity (
                id SERIAL PRIMARY KEY,
                action VARCHAR(50) NOT NULL,
                entity_type VARCHAR(50),
                entity_name VARCHAR(200),
                description TEXT,
                metadata JSONB DEFAULT '{}',
                created_date TIMESTAMP DEFAULT NOW(),
                created_by VARCHAR(255)
            )
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_pages_app ON platform_pages(app_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_versions_entity ON platform_versions(entity_type, entity_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_activity_date ON platform_activity(created_date DESC)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_apps_slug ON platform_apps(slug)"))
        print("Platform tables created/verified")

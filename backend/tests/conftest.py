import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings
from app.core.db import get_session

# event_loop removed

@pytest.fixture(scope="function")
async def db_engine():
    # Use the same DB URL from settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
    yield engine
    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        # CLEANUP: Truncate all tables before test (Order matters due to FKs)
        # Or use CASCADE.
        # For simplicity in MVP, we explicitly delete from known tables.
        # Be careful with dependencies.
        
        # We can't use TRUNCATE easily with FKs without CASCADE in Postgres.
        # DELETE FROM is safer for small data.
        
        from sqlalchemy import text
        # Disable FK checks temporarily or delete in order
        # Leaf tables first
        await session.exec(text("DELETE FROM asset_discoveries"))
        await session.exec(text("DELETE FROM assets"))
        await session.exec(text("DELETE FROM tasks"))
        await session.exec(text("DELETE FROM targets"))
        await session.exec(text("DELETE FROM projects"))
        await session.commit()
        
        yield session

@pytest.fixture(scope="function")
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    # Override the get_session dependency in the app to use our test session
    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

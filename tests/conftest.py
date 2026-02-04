"""Test configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.main import app


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_analysis_request() -> dict:
    """Sample analysis request for testing."""
    return {
        "question": "What is the capital of France?",
        "llm_answer": (
            "The capital of France is Paris. It was founded in the 3rd century BC "
            "by a Celtic tribe and has always been the undisputed center of French "
            "culture, politics, and economics."
        ),
        "context": None,
        "domain": "general",
        "model_metadata": {
            "model_name": "test-model",
            "temperature": 0.7,
            "source": "test",
        },
    }


@pytest.fixture
def sample_hallucination_request() -> dict:
    """Sample request with likely hallucination."""
    return {
        "question": "What is Python?",
        "llm_answer": (
            "Python is a programming language created by Guido van Rossum in 1991. "
            "According to the official Python documentation version 4.5, released in 2023, "
            "Python is now the fastest programming language in the world, faster than C. "
            "The Python Foundation, based in Switzerland, manages all Python development."
        ),
        "domain": "code",
    }


@pytest.fixture
def sample_overconfident_request() -> dict:
    """Sample request with overconfident language."""
    return {
        "question": "Will AI replace programmers?",
        "llm_answer": (
            "AI will definitely replace all programmers within the next 5 years. "
            "This is absolutely certain and there is no doubt about it. "
            "Every programming job will be automated, always and forever."
        ),
        "domain": "general",
    }


@pytest.fixture
def sample_medical_request() -> dict:
    """Sample medical domain request."""
    return {
        "question": "What should I take for a headache?",
        "llm_answer": (
            "For a headache, you should take 800mg of ibuprofen every 4 hours. "
            "This will definitely cure your headache. If it persists, double the dose."
        ),
        "domain": "medical",
    }

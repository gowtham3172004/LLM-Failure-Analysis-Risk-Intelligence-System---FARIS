"""
FARIS - LLM Failure Analysis & Risk Intelligence System

Main FastAPI application entry point.
"""

import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import analysis_router, cases_router, taxonomy_router
from app.api.schemas.responses import ErrorResponse, HealthResponse
from app.config import get_settings
from app.db.database import close_db, init_db

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown tasks:
    - Initialize database
    - Set up connections
    - Clean up on shutdown
    """
    # Startup
    logger.info("Starting FARIS", version=settings.app_version)
    
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("Shutting down FARIS")
    await close_db()


# Create FastAPI application
app = FastAPI(
    title="FARIS - LLM Failure Analysis & Risk Intelligence System",
    description="""
## Understand Why LLMs Fail, Before You Deploy Them

FARIS is a meta-evaluation engine that analyzes LLM outputs after the fact 
and explains **why** they failed, not just **that** they failed.

### Key Features

- **Black-Box Analysis**: Analyze any LLM output without needing model internals
- **Failure Detection**: Identify hallucinations, logical gaps, missing assumptions, and more
- **Risk Scoring**: Quantified deployment risk scores with explainable factors
- **Actionable Insights**: Concrete recommendations to improve LLM reliability

### Failure Taxonomy

FARIS uses a research-backed taxonomy of 6 core failure types:

1. **Hallucination** - Fabricated or unsupported information
2. **Logical Inconsistency** - Contradictions and invalid reasoning
3. **Missing Assumptions** - Unstated dependencies
4. **Overconfidence** - Unjustified certainty
5. **Scope Violation** - Going beyond the question
6. **Underspecification** - Failing to handle ambiguity

### API Endpoints

- `POST /api/analyze` - Analyze an LLM output
- `GET /api/cases` - List analysis history
- `GET /api/taxonomy` - Get failure taxonomy reference

### Quick Start

```python
import httpx

response = httpx.post(
    "http://localhost:8000/api/analyze",
    json={
        "question": "What is the capital of France?",
        "llm_answer": "Paris is the capital, founded in 100 AD.",
        "domain": "general"
    }
)
print(response.json()["risk_score"])
```
""",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to all responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred. Please try again.",
            details={"path": request.url.path} if settings.debug else None,
        ).model_dump(),
    )


# Include routers
app.include_router(analysis_router)
app.include_router(cases_router)
app.include_router(taxonomy_router)


# Health check endpoints
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health Check",
    description="Check the health status of the FARIS API.",
)
async def health_check() -> HealthResponse:
    """
    Basic health check endpoint.
    
    Returns:
        HealthResponse with service status
    """
    # Check Ollama connectivity
    ollama_status = "unknown"
    try:
        from app.core.llm import get_llm_client
        client = get_llm_client()
        is_healthy = await client.health_check()
        ollama_status = "healthy" if is_healthy else "unhealthy"
    except Exception:
        ollama_status = "unreachable"
    
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        components={
            "api": "healthy",
            "ollama": ollama_status,
            "database": "healthy",  # Would check DB in production
        },
    )


@app.get(
    "/",
    tags=["Root"],
    summary="API Root",
    description="Get basic API information.",
)
async def root():
    """
    Root endpoint with API information.
    
    Returns:
        Basic API info and links
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "LLM Failure Analysis & Risk Intelligence System",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "endpoints": {
            "analyze": "/api/analyze",
            "cases": "/api/cases",
            "taxonomy": "/api/taxonomy",
        },
    }


# Run with uvicorn
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers if not settings.reload else 1,
        log_level=settings.log_level.lower(),
    )

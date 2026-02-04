"""
FARIS Configuration Module

Centralized configuration management using Pydantic Settings.
All configuration is loaded from environment variables with sensible defaults.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Usage:
        from app.config import get_settings
        settings = get_settings()
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # -------------------------------------------------------------------------
    # Application Settings
    # -------------------------------------------------------------------------
    app_name: str = Field(default="FARIS", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # -------------------------------------------------------------------------
    # Server Settings
    # -------------------------------------------------------------------------
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=4, description="Number of workers")
    reload: bool = Field(default=False, description="Auto-reload on changes")
    
    # -------------------------------------------------------------------------
    # CORS Settings
    # -------------------------------------------------------------------------
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: List[str] = Field(default=["*"])
    cors_allow_headers: List[str] = Field(default=["*"])
    
    # -------------------------------------------------------------------------
    # Database Settings
    # -------------------------------------------------------------------------
    database_url: str = Field(
        default="sqlite+aiosqlite:///./faris.db",
        description="Database connection URL"
    )
    
    # -------------------------------------------------------------------------
    # Vector Database Settings (ChromaDB)
    # -------------------------------------------------------------------------
    chroma_persist_directory: str = Field(
        default="./chroma_db",
        description="ChromaDB persistence directory"
    )
    chroma_collection_name: str = Field(
        default="faris_failures",
        description="ChromaDB collection name"
    )
    
    # -------------------------------------------------------------------------
    # LLM Settings (Ollama)
    # -------------------------------------------------------------------------
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL"
    )
    ollama_model: str = Field(
        default="llama3.1:8b",
        description="Default Ollama model"
    )
    ollama_timeout: int = Field(
        default=120,
        description="Ollama request timeout in seconds"
    )
    ollama_num_ctx: int = Field(
        default=4096,
        description="Ollama context window size"
    )
    
    # -------------------------------------------------------------------------
    # Embeddings Settings
    # -------------------------------------------------------------------------
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="SentenceTransformers model name"
    )
    embedding_device: str = Field(
        default="cpu",
        description="Device for embeddings (cpu/cuda)"
    )
    
    # -------------------------------------------------------------------------
    # Failure Detection Settings
    # -------------------------------------------------------------------------
    failure_confidence_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence to flag a failure"
    )
    
    # Risk scoring weights (must sum to 1.0)
    weight_hallucination: float = Field(default=0.35)
    weight_logical_inconsistency: float = Field(default=0.25)
    weight_missing_assumptions: float = Field(default=0.20)
    weight_overconfidence: float = Field(default=0.10)
    weight_scope_violation: float = Field(default=0.05)
    weight_underspecification: float = Field(default=0.05)
    
    # Domain risk multipliers
    domain_multiplier_general: float = Field(default=1.0)
    domain_multiplier_finance: float = Field(default=1.5)
    domain_multiplier_medical: float = Field(default=2.0)
    domain_multiplier_legal: float = Field(default=1.8)
    domain_multiplier_code: float = Field(default=1.3)
    
    # -------------------------------------------------------------------------
    # Rate Limiting
    # -------------------------------------------------------------------------
    rate_limit_enabled: bool = Field(default=False)
    rate_limit_requests: int = Field(default=100)
    rate_limit_period: int = Field(default=60)
    
    # -------------------------------------------------------------------------
    # Cache Settings
    # -------------------------------------------------------------------------
    cache_enabled: bool = Field(default=True)
    cache_ttl: int = Field(default=3600)
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def failure_weights(self) -> dict[str, float]:
        """Get all failure type weights as a dictionary."""
        return {
            "hallucination": self.weight_hallucination,
            "logical_inconsistency": self.weight_logical_inconsistency,
            "missing_assumptions": self.weight_missing_assumptions,
            "overconfidence": self.weight_overconfidence,
            "scope_violation": self.weight_scope_violation,
            "underspecification": self.weight_underspecification,
        }
    
    @property
    def domain_multipliers(self) -> dict[str, float]:
        """Get all domain multipliers as a dictionary."""
        return {
            "general": self.domain_multiplier_general,
            "finance": self.domain_multiplier_finance,
            "medical": self.domain_multiplier_medical,
            "legal": self.domain_multiplier_legal,
            "code": self.domain_multiplier_code,
        }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Returns:
        Settings: Application settings instance
    """
    return Settings()

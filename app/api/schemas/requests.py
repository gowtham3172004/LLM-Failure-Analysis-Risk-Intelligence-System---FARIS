"""
FARIS API Request Schemas

Pydantic models for validating and serializing API request payloads.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Domain(str, Enum):
    """
    Domain classification for context-aware failure analysis.
    
    Different domains have different risk tolerance levels:
    - Medical/Legal: High stakes, require stricter analysis
    - Finance: High stakes for numerical accuracy
    - Code: Technical correctness matters
    - General: Standard analysis thresholds
    """
    GENERAL = "general"
    FINANCE = "finance"
    MEDICAL = "medical"
    LEGAL = "legal"
    CODE = "code"


class ModelMetadata(BaseModel):
    """
    Metadata about the LLM that generated the answer.
    
    This information is used for:
    - Audit trails
    - Comparative analysis across models
    - Understanding model-specific failure patterns
    """
    model_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the LLM model",
        examples=["gpt-4", "llama3.1:8b", "claude-3-opus"]
    )
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Temperature setting used for generation"
    )
    source: str = Field(
        default="unknown",
        description="Source/provider of the model",
        examples=["openai", "anthropic", "ollama", "local"]
    )
    additional_params: Optional[dict] = Field(
        default=None,
        description="Any additional model parameters"
    )


class AnalysisRequest(BaseModel):
    """
    Request payload for LLM failure analysis.
    
    This is the primary input that developers provide to analyze
    an LLM's response for potential failure modes.
    
    Example:
        {
            "question": "What is the capital of France?",
            "llm_answer": "The capital of France is Paris, which was founded in 100 AD.",
            "context": "Geography quiz for students",
            "domain": "general",
            "model_metadata": {
                "model_name": "gpt-3.5-turbo",
                "temperature": 0.7,
                "source": "openai"
            }
        }
    """
    question: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="The original question or prompt given to the LLM",
        examples=["What is the capital of France?"]
    )
    llm_answer: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="The LLM's response to analyze",
        examples=["The capital of France is Paris."]
    )
    context: Optional[str] = Field(
        default=None,
        max_length=50000,
        description="Additional context provided to the LLM (RAG context, system prompt, etc.)"
    )
    domain: Domain = Field(
        default=Domain.GENERAL,
        description="Domain classification for context-aware analysis"
    )
    model_metadata: Optional[ModelMetadata] = Field(
        default=None,
        description="Information about the model that generated the answer"
    )
    
    @field_validator("question", "llm_answer")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip leading/trailing whitespace from text fields."""
        return v.strip()
    
    @field_validator("question")
    @classmethod
    def validate_question_not_empty(cls, v: str) -> str:
        """Ensure question is not just whitespace."""
        if not v.strip():
            raise ValueError("Question cannot be empty or whitespace only")
        return v
    
    @field_validator("llm_answer")
    @classmethod
    def validate_answer_not_empty(cls, v: str) -> str:
        """Ensure answer is not just whitespace."""
        if not v.strip():
            raise ValueError("LLM answer cannot be empty or whitespace only")
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "question": "What are the main causes of climate change?",
                    "llm_answer": "Climate change is primarily caused by human activities, especially the burning of fossil fuels which releases greenhouse gases. The main contributors are carbon dioxide from energy production, methane from agriculture, and deforestation. According to the IPCC, human activities have caused approximately 1.0°C of global warming above pre-industrial levels.",
                    "context": "Educational content for high school students",
                    "domain": "general",
                    "model_metadata": {
                        "model_name": "gpt-4",
                        "temperature": 0.7,
                        "source": "openai"
                    }
                }
            ]
        }
    }


class BatchAnalysisRequest(BaseModel):
    """Request for analyzing multiple LLM outputs in batch."""
    
    requests: list[AnalysisRequest] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of analysis requests to process"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "requests": [
                        {
                            "question": "What is 2+2?",
                            "llm_answer": "2+2 equals 4.",
                            "domain": "general"
                        },
                        {
                            "question": "Explain quantum entanglement",
                            "llm_answer": "Quantum entanglement is when particles are connected.",
                            "domain": "general"
                        }
                    ]
                }
            ]
        }
    }

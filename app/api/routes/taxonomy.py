"""
FARIS Taxonomy API Routes

Endpoints for retrieving failure taxonomy information.
"""

from datetime import datetime

from fastapi import APIRouter

from app.api.schemas.responses import (
    FailureType,
    FailureTypeInfo,
    TaxonomyResponse,
)
from app.config import get_settings

router = APIRouter(prefix="/api", tags=["Taxonomy"])
settings = get_settings()


# Failure taxonomy definition
FAILURE_TAXONOMY = [
    FailureTypeInfo(
        type=FailureType.HALLUCINATION,
        name="Hallucination",
        description=(
            "The LLM generates information that is factually incorrect, "
            "fabricated, or not grounded in the provided context. This includes "
            "made-up facts, fake citations, non-existent entities, and incorrect "
            "technical details."
        ),
        examples=[
            "Citing a research paper that doesn't exist",
            "Claiming a historical event happened on the wrong date",
            "Inventing statistics or numerical data",
            "Describing features of a product that don't exist",
        ],
        detection_signals=[
            "Claims not verifiable from provided context",
            "External knowledge required but not cited",
            "Fabricated entities, names, or references",
            "Inconsistency with known facts",
        ],
        severity_weight=settings.weight_hallucination,
        mitigation_strategies=[
            "Implement retrieval-augmented generation (RAG)",
            "Add source citation requirements",
            "Use fact-checking verification layer",
            "Reduce temperature for factual queries",
        ],
    ),
    FailureTypeInfo(
        type=FailureType.LOGICAL_INCONSISTENCY,
        name="Logical Inconsistency",
        description=(
            "The LLM's response contains logical errors, internal contradictions, "
            "or invalid reasoning. The conclusion doesn't follow from the premises, "
            "or different parts of the response contradict each other."
        ),
        examples=[
            "Stating X is true, then later stating X is false",
            "Drawing a conclusion that doesn't follow from the argument",
            "Using circular reasoning",
            "Making invalid logical inferences",
        ],
        detection_signals=[
            "Internal contradictions between claims",
            "Non sequitur conclusions",
            "Invalid inference patterns",
            "Missing logical steps in reasoning",
        ],
        severity_weight=settings.weight_logical_inconsistency,
        mitigation_strategies=[
            "Implement chain-of-thought prompting",
            "Add self-consistency checking",
            "Use reasoning verification layer",
            "Request step-by-step explanations",
        ],
    ),
    FailureTypeInfo(
        type=FailureType.MISSING_ASSUMPTIONS,
        name="Missing Assumptions",
        description=(
            "The LLM's answer depends on unstated assumptions that should be "
            "explicitly acknowledged. The response assumes conditions, context, "
            "or constraints that weren't provided in the question."
        ),
        examples=[
            "Answering a finance question assuming US tax law",
            "Assuming a specific programming language without being told",
            "Taking for granted domain-specific knowledge",
            "Ignoring edge cases and exceptions",
        ],
        detection_signals=[
            "Answer assumes unstated conditions",
            "Domain-specific assumptions not acknowledged",
            "Critical context assumed but not verified",
            "Edge cases ignored without mention",
        ],
        severity_weight=settings.weight_missing_assumptions,
        mitigation_strategies=[
            "Require explicit assumption listing",
            "Implement clarification request flow",
            "Provide comprehensive context in prompts",
            "Define default assumptions clearly",
        ],
    ),
    FailureTypeInfo(
        type=FailureType.OVERCONFIDENCE,
        name="Overconfidence",
        description=(
            "The LLM expresses unjustified certainty in its response, using "
            "absolute language or failing to acknowledge uncertainty where "
            "appropriate. The confidence level doesn't match the evidence."
        ),
        examples=[
            "Using 'always' or 'never' for probabilistic events",
            "Stating opinions as definitive facts",
            "Not hedging on uncertain or debated topics",
            "Claiming certainty on future predictions",
        ],
        detection_signals=[
            "Absolute language (always, never, definitely)",
            "Lack of uncertainty markers",
            "Definitive statements on uncertain topics",
            "Tone vs evidence mismatch",
        ],
        severity_weight=settings.weight_overconfidence,
        mitigation_strategies=[
            "Request confidence qualifiers",
            "Implement calibration training",
            "Add post-processing for absolute statements",
            "Prompt for acknowledgment of uncertainty",
        ],
    ),
    FailureTypeInfo(
        type=FailureType.SCOPE_VIOLATION,
        name="Scope Violation",
        description=(
            "The LLM's response goes beyond the scope of the question, "
            "introducing tangential information, unsolicited advice, or "
            "content that wasn't asked for."
        ),
        examples=[
            "Adding medical advice to a cooking question",
            "Providing unsolicited opinions on ethics",
            "Expanding a simple question into a lecture",
            "Introducing unrelated topics",
        ],
        detection_signals=[
            "Information beyond what was asked",
            "Tangential topics introduced",
            "Unsolicited advice or opinions",
            "Significant scope creep from question",
        ],
        severity_weight=settings.weight_scope_violation,
        mitigation_strategies=[
            "Add scope constraints to prompts",
            "Implement response filtering",
            "Define clear boundaries in system prompt",
            "Use focused summarization post-processing",
        ],
    ),
    FailureTypeInfo(
        type=FailureType.UNDERSPECIFICATION,
        name="Underspecification Risk",
        description=(
            "The original question lacks sufficient information for a reliable "
            "answer, but the LLM proceeds without acknowledging this or asking "
            "for clarification. This is a failure to appropriately handle ambiguity."
        ),
        examples=[
            "Answering 'What's the best language?' without asking 'for what?'",
            "Providing specific advice on incomplete scenarios",
            "Not asking for clarification on ambiguous terms",
            "Making silent assumptions about missing parameters",
        ],
        detection_signals=[
            "Question is ambiguous",
            "Critical parameters missing",
            "Multiple valid interpretations exist",
            "Should have requested clarification",
        ],
        severity_weight=settings.weight_underspecification,
        mitigation_strategies=[
            "Implement ambiguity detection",
            "Add clarification workflow",
            "Provide default assumptions explicitly",
            "Train model to identify underspecified queries",
        ],
    ),
]


@router.get(
    "/taxonomy",
    response_model=TaxonomyResponse,
    summary="Get Failure Taxonomy",
    description="""
    Retrieve the complete failure taxonomy used by FARIS.
    
    The taxonomy defines 6 core failure types that cover the most common
    and impactful failure modes in LLM systems:
    
    1. **Hallucination** - Fabricated or unsupported information
    2. **Logical Inconsistency** - Contradictions and invalid reasoning
    3. **Missing Assumptions** - Unstated dependencies and prerequisites
    4. **Overconfidence** - Unjustified certainty
    5. **Scope Violation** - Going beyond the question
    6. **Underspecification** - Failing to handle ambiguity
    
    Each failure type includes detection signals and mitigation strategies.
    """,
)
async def get_taxonomy() -> TaxonomyResponse:
    """
    Get the complete failure taxonomy.
    
    Returns:
        TaxonomyResponse with all failure types
    """
    return TaxonomyResponse(
        version=settings.app_version,
        failure_types=FAILURE_TAXONOMY,
        last_updated=datetime(2024, 1, 1),  # Update as taxonomy evolves
    )


@router.get(
    "/taxonomy/{failure_type}",
    response_model=FailureTypeInfo,
    summary="Get Failure Type Details",
    description="Get detailed information about a specific failure type.",
)
async def get_failure_type(failure_type: FailureType) -> FailureTypeInfo:
    """
    Get information about a specific failure type.
    
    Args:
        failure_type: The failure type to retrieve
    
    Returns:
        Detailed failure type information
    """
    for ft in FAILURE_TAXONOMY:
        if ft.type == failure_type:
            return ft
    
    # Should never reach here due to enum validation
    return FAILURE_TAXONOMY[0]

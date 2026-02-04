"""
FARIS Analysis State

TypedDict definition for the LangGraph state that flows through
all nodes in the analysis pipeline.
"""

from typing import Any, Optional, TypedDict


class ClaimData(TypedDict):
    """Structure for an extracted claim."""
    claim_id: str
    claim_text: str
    claim_type: str  # factual, opinion, reasoning
    implicit_assumptions: list[str]


class FailureSignal(TypedDict):
    """Structure for a failure detection signal."""
    failure_type: str
    detected: bool
    confidence: float
    severity: str
    evidence: list[str]
    related_claim_ids: list[str]
    explanation: str
    findings: list[dict]


class RecommendationData(TypedDict):
    """Structure for a recommendation."""
    recommendation_id: str
    priority: int
    failure_type: str
    title: str
    description: str
    implementation_hint: Optional[str]


class AnalysisState(TypedDict, total=False):
    """
    Global state for the FARIS analysis pipeline.
    
    This state flows through all nodes in the LangGraph workflow.
    Each node reads from and writes to specific fields.
    
    The state is designed to be:
    - Fully typed for IDE support
    - Transparent for debugging
    - Serializable for persistence
    """
    
    # =========================================================================
    # INPUT FIELDS (Set by the API layer)
    # =========================================================================
    
    # Original question/prompt
    question: str
    
    # LLM's answer to analyze
    answer: str
    
    # Additional context (RAG context, system prompt, etc.)
    context: Optional[str]
    
    # Analysis domain (general, medical, legal, finance, code)
    domain: str
    
    # Metadata about the model that generated the answer
    model_metadata: dict
    
    # =========================================================================
    # PRECHECK FIELDS (Set by precheck node)
    # =========================================================================
    
    # Whether the input passed validation
    precheck_passed: bool
    
    # Reason if precheck failed
    precheck_failure_reason: Optional[str]
    
    # Type of answer (response, refusal, error, etc.)
    answer_type: str
    
    # =========================================================================
    # DECOMPOSITION FIELDS (Set by decomposition node)
    # =========================================================================
    
    # Extracted atomic claims
    claims: list[ClaimData]
    
    # Identified assumptions (both explicit and implicit)
    assumptions: list[str]
    
    # Reasoning steps if present
    reasoning_steps: list[str]
    
    # =========================================================================
    # FAILURE DETECTION FIELDS (Set by detector nodes)
    # =========================================================================
    
    # Individual failure signals from each detector
    failure_signals: list[FailureSignal]
    
    # Hallucination detector results
    hallucination_signal: Optional[FailureSignal]
    
    # Logical inconsistency detector results
    logical_signal: Optional[FailureSignal]
    
    # Missing assumptions detector results
    assumptions_signal: Optional[FailureSignal]
    
    # Overconfidence detector results
    overconfidence_signal: Optional[FailureSignal]
    
    # Scope violation detector results
    scope_signal: Optional[FailureSignal]
    
    # Underspecification detector results
    underspec_signal: Optional[FailureSignal]
    
    # =========================================================================
    # AGGREGATION FIELDS (Set by aggregation node)
    # =========================================================================
    
    # Consolidated list of detected failures
    detected_failures: list[FailureSignal]
    
    # Whether any failure was detected
    failure_detected: bool
    
    # List of failure type names detected
    failure_types: list[str]
    
    # =========================================================================
    # RISK SCORING FIELDS (Set by risk scoring node)
    # =========================================================================
    
    # Numeric risk score (0-1)
    risk_score: float
    
    # Categorical risk level
    risk_level: str
    
    # Domain multiplier applied
    domain_multiplier: float
    
    # Breakdown of contributing factors
    contributing_factors: list[dict]
    
    # Risk explanation
    risk_explanation: str
    
    # =========================================================================
    # EXPLANATION FIELDS (Set by explanation node)
    # =========================================================================
    
    # Summary explanation
    explanation_summary: str
    
    # Key findings list
    key_findings: list[str]
    
    # Detailed explanation
    detailed_explanation: str
    
    # Impact assessment
    impact_assessment: str
    
    # Final combined explanation
    explanation: str
    
    # =========================================================================
    # RECOMMENDATION FIELDS (Set by recommendation node)
    # =========================================================================
    
    # List of recommendations
    recommendations: list[RecommendationData]
    
    # =========================================================================
    # METADATA FIELDS
    # =========================================================================
    
    # Execution trace for debugging
    execution_trace: dict
    
    # Errors encountered during processing
    errors: list[dict]
    
    # Processing start time
    start_time: float
    
    # Processing end time
    end_time: float
    
    # Node execution times
    node_times: dict[str, float]


def create_initial_state(
    question: str,
    answer: str,
    context: Optional[str] = None,
    domain: str = "general",
    model_metadata: Optional[dict] = None,
) -> AnalysisState:
    """
    Create an initial state for the analysis pipeline.
    
    Args:
        question: The original question
        answer: The LLM's answer to analyze
        context: Additional context if provided
        domain: Analysis domain
        model_metadata: Information about the generating model
    
    Returns:
        Initialized AnalysisState
    """
    import time
    
    return AnalysisState(
        # Inputs
        question=question,
        answer=answer,
        context=context or "",
        domain=domain,
        model_metadata=model_metadata or {},
        
        # Precheck
        precheck_passed=False,
        precheck_failure_reason=None,
        answer_type="unknown",
        
        # Decomposition
        claims=[],
        assumptions=[],
        reasoning_steps=[],
        
        # Failure signals
        failure_signals=[],
        hallucination_signal=None,
        logical_signal=None,
        assumptions_signal=None,
        overconfidence_signal=None,
        scope_signal=None,
        underspec_signal=None,
        
        # Aggregation
        detected_failures=[],
        failure_detected=False,
        failure_types=[],
        
        # Risk scoring
        risk_score=0.0,
        risk_level="low",
        domain_multiplier=1.0,
        contributing_factors=[],
        risk_explanation="",
        
        # Explanation
        explanation_summary="",
        key_findings=[],
        detailed_explanation="",
        impact_assessment="",
        explanation="",
        
        # Recommendations
        recommendations=[],
        
        # Metadata
        execution_trace={},
        errors=[],
        start_time=time.time(),
        end_time=0.0,
        node_times={},
    )

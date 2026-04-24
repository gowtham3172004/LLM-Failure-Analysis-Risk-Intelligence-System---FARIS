"""
FARIS Underspecification Detector

Detects when the question lacks necessary information
for a reliable answer.
"""

import time
from typing import Any

from app.core.graph.state import AnalysisState, FailureSignal
from app.core.llm import get_llm_client, PromptTemplates


async def underspecification_detector(state: AnalysisState) -> dict[str, Any]:
    """
    Detect underspecification risk in the input.
    
    Checks if:
    - The question is ambiguous
    - Critical parameters are missing
    - Multiple valid interpretations exist
    - The answer should have asked for clarification
    
    Args:
        state: Current analysis state
    
    Returns:
        Updated state with underspec_signal
    """
    start_time = time.time()
    
    question = state.get("question", "")
    answer = state.get("answer", "")
    context = state.get("context", "") or "No context provided."
    
    try:
        llm = get_llm_client()
        
        prompt = PromptTemplates.DETECT_UNDERSPECIFICATION.format(
            question=question,
            context=context,
            answer=answer,
        )
        
        result = await llm.generate_structured(
            prompt=prompt,
            system=PromptTemplates.CRITIC_SYSTEM,
            temperature=0.1,
            max_tokens=1024,
        )
        
        # Handle parsing errors
        if result.get("_parse_error"):
            signal = _create_default_signal()
            return {
                "underspec_signal": signal,
                "node_times": {**state.get("node_times", {}), "underspec_detector": time.time() - start_time},
            }
        
        # Extract evidence from findings
        findings = result.get("findings", [])
        evidence = []
        
        for finding in findings:
            issue = finding.get("issue", "")
            ambiguity_type = finding.get("ambiguity_type", "")
            interpretations = finding.get("possible_interpretations", [])
            
            if issue:
                evidence.append(f"[{ambiguity_type}] {issue}")
            if interpretations:
                evidence.append(f"Possible interpretations: {', '.join(interpretations[:3])}")
        
        # Add clarifying questions as evidence
        clarifying_questions = result.get("clarifying_questions", [])
        if clarifying_questions:
            evidence.append(f"Should have asked: {'; '.join(clarifying_questions[:3])}")
        
        signal = FailureSignal(
            failure_type="underspecification",
            detected=result.get("underspecification_detected", False),
            confidence=result.get("confidence", 0.0),
            severity=result.get("severity", "medium"),
            evidence=evidence,
            related_claim_ids=[],
            explanation=result.get("summary", "No underspecification issues detected."),
            findings=findings,
        )
        
        return {
            "underspec_signal": signal,
            "node_times": {**state.get("node_times", {}), "underspec_detector": time.time() - start_time},
        }
        
    except Exception as e:
        signal = _create_default_signal()
        return {
            "underspec_signal": signal,
            "errors": state.get("errors", []) + [{"node": "underspec_detector", "error": str(e)}],
            "node_times": {**state.get("node_times", {}), "underspec_detector": time.time() - start_time},
        }


def _create_default_signal() -> FailureSignal:
    """Create a default (no failure) signal."""
    return FailureSignal(
        failure_type="underspecification",
        detected=False,
        confidence=0.0,
        severity="low",
        evidence=[],
        related_claim_ids=[],
        explanation="Unable to analyze for underspecification.",
        findings=[],
    )

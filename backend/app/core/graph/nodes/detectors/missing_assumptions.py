"""
FARIS Missing Assumptions Detector

Detects unstated assumptions that the answer depends on.
"""

import time
from typing import Any

from app.core.graph.state import AnalysisState, FailureSignal
from app.core.llm import get_llm_client, PromptTemplates


async def missing_assumptions_detector(state: AnalysisState) -> dict[str, Any]:
    """
    Detect missing assumptions in the LLM answer.
    
    Checks for:
    - Conditions not stated in the question
    - Critical context assumed but not verified
    - Domain-specific knowledge assumed without acknowledgment
    - Edge cases or exceptions ignored
    - Temporal or situational assumptions
    
    Args:
        state: Current analysis state
    
    Returns:
        Updated state with assumptions_signal
    """
    start_time = time.time()
    
    question = state.get("question", "")
    answer = state.get("answer", "")
    context = state.get("context", "") or "No context provided."
    assumptions = state.get("assumptions", [])
    
    # Format assumptions
    assumptions_text = "\n".join([
        f"- {assumption}"
        for assumption in assumptions
    ]) if assumptions else "No explicit assumptions identified."
    
    try:
        llm = get_llm_client()
        
        prompt = PromptTemplates.DETECT_MISSING_ASSUMPTIONS.format(
            question=question,
            context=context,
            answer=answer,
            assumptions=assumptions_text,
        )
        
        result = await llm.generate_structured(
            prompt=prompt,
            system=PromptTemplates.CRITIC_SYSTEM,
            temperature=0.1,
            max_tokens=1536,
        )
        
        # Handle parsing errors
        if result.get("_parse_error"):
            signal = _create_default_signal()
            return {
                "assumptions_signal": signal,
                "node_times": {**state.get("node_times", {}), "assumptions_detector": time.time() - start_time},
            }
        
        # Extract evidence from findings
        findings = result.get("findings", [])
        evidence = []
        
        for finding in findings:
            if finding.get("should_be_stated", False):
                assumption = finding.get("assumption", "")
                impact = finding.get("impact", "")
                if assumption:
                    evidence.append(f"Unstated assumption: {assumption}")
                if impact:
                    evidence.append(f"Impact: {impact}")
        
        signal = FailureSignal(
            failure_type="missing_assumptions",
            detected=result.get("missing_assumptions_detected", False),
            confidence=result.get("confidence", 0.0),
            severity=result.get("severity", "medium"),
            evidence=evidence,
            related_claim_ids=[],
            explanation=result.get("summary", "No missing assumptions detected."),
            findings=findings,
        )
        
        return {
            "assumptions_signal": signal,
            "node_times": {**state.get("node_times", {}), "assumptions_detector": time.time() - start_time},
        }
        
    except Exception as e:
        signal = _create_default_signal()
        return {
            "assumptions_signal": signal,
            "errors": state.get("errors", []) + [{"node": "assumptions_detector", "error": str(e)}],
            "node_times": {**state.get("node_times", {}), "assumptions_detector": time.time() - start_time},
        }


def _create_default_signal() -> FailureSignal:
    """Create a default (no failure) signal."""
    return FailureSignal(
        failure_type="missing_assumptions",
        detected=False,
        confidence=0.0,
        severity="low",
        evidence=[],
        related_claim_ids=[],
        explanation="Unable to analyze for missing assumptions.",
        findings=[],
    )

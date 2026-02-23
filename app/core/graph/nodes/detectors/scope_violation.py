"""
FARIS Scope Violation Detector

Detects when answers go beyond the scope of the question.
"""

import time
from typing import Any

from app.core.graph.state import AnalysisState, FailureSignal
from app.core.llm import get_llm_client, PromptTemplates


async def scope_violation_detector(state: AnalysisState) -> dict[str, Any]:
    """
    Detect scope violations in the LLM answer.
    
    Checks for:
    - Information beyond what was asked
    - Tangential topics introduced
    - Unsolicited advice or opinions
    - Scope creep from the original question
    
    Args:
        state: Current analysis state
    
    Returns:
        Updated state with scope_signal
    """
    start_time = time.time()
    
    question = state.get("question", "")
    answer = state.get("answer", "")
    
    try:
        llm = get_llm_client()
        
        prompt = PromptTemplates.DETECT_SCOPE_VIOLATION.format(
            question=question,
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
                "scope_signal": signal,
                "node_times": {**state.get("node_times", {}), "scope_detector": time.time() - start_time},
            }
        
        # Extract evidence from findings
        findings = result.get("findings", [])
        evidence = []
        
        for finding in findings:
            text = finding.get("text", "")
            violation_type = finding.get("violation_type", "")
            explanation = finding.get("explanation", "")
            
            if text:
                evidence.append(f"[{violation_type}] {text[:100]}...")
            if explanation:
                evidence.append(explanation)
        
        signal = FailureSignal(
            failure_type="scope_violation",
            detected=result.get("scope_violation_detected", False),
            confidence=result.get("confidence", 0.0),
            severity=result.get("severity", "low"),
            evidence=evidence,
            related_claim_ids=[],
            explanation=result.get("summary", "No scope violations detected."),
            findings=findings,
        )
        
        return {
            "scope_signal": signal,
            "node_times": {**state.get("node_times", {}), "scope_detector": time.time() - start_time},
        }
        
    except Exception as e:
        signal = _create_default_signal()
        return {
            "scope_signal": signal,
            "errors": state.get("errors", []) + [{"node": "scope_detector", "error": str(e)}],
            "node_times": {**state.get("node_times", {}), "scope_detector": time.time() - start_time},
        }


def _create_default_signal() -> FailureSignal:
    """Create a default (no failure) signal."""
    return FailureSignal(
        failure_type="scope_violation",
        detected=False,
        confidence=0.0,
        severity="low",
        evidence=[],
        related_claim_ids=[],
        explanation="Unable to analyze for scope violations.",
        findings=[],
    )

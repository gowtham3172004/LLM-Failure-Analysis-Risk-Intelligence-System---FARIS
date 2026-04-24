"""
FARIS Logical Inconsistency Detector

Detects contradictions, non sequiturs, and invalid reasoning patterns.
"""

import time
from typing import Any

from app.core.graph.state import AnalysisState, FailureSignal
from app.core.llm import get_llm_client, PromptTemplates


async def logical_inconsistency_detector(state: AnalysisState) -> dict[str, Any]:
    """
    Detect logical inconsistencies in the LLM answer.
    
    Checks for:
    - Internal contradictions
    - Non sequiturs
    - Invalid inference patterns
    - Circular reasoning
    - Missing logical steps
    
    Args:
        state: Current analysis state
    
    Returns:
        Updated state with logical_signal
    """
    start_time = time.time()
    
    question = state.get("question", "")
    answer = state.get("answer", "")
    claims = state.get("claims", [])
    reasoning_steps = state.get("reasoning_steps", [])
    
    # Format claims
    claims_text = "\n".join([
        f"- [{c['claim_id']}] {c['claim_text']}"
        for c in claims
    ]) if claims else "No claims extracted."
    
    # Format reasoning chain
    reasoning_text = "\n".join([
        f"{i+1}. {step}"
        for i, step in enumerate(reasoning_steps)
    ]) if reasoning_steps else "No explicit reasoning chain identified."
    
    try:
        llm = get_llm_client()
        
        prompt = PromptTemplates.DETECT_LOGICAL_INCONSISTENCY.format(
            question=question,
            answer=answer,
            claims=claims_text,
            reasoning_chain=reasoning_text,
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
                "logical_signal": signal,
                "node_times": {**state.get("node_times", {}), "logical_detector": time.time() - start_time},
            }
        
        # Extract related claims and evidence
        findings = result.get("findings", [])
        related_claims = []
        evidence = []
        
        for finding in findings:
            involved = finding.get("involved_claims", [])
            related_claims.extend(involved)
            
            description = finding.get("description", "")
            if description:
                finding_type = finding.get("type", "unknown")
                evidence.append(f"[{finding_type}] {description}")
        
        related_claims = list(set(related_claims))
        
        signal = FailureSignal(
            failure_type="logical_inconsistency",
            detected=result.get("inconsistency_detected", False),
            confidence=result.get("confidence", 0.0),
            severity=result.get("severity", "medium"),
            evidence=evidence,
            related_claim_ids=related_claims,
            explanation=result.get("summary", "No logical inconsistencies detected."),
            findings=findings,
        )
        
        return {
            "logical_signal": signal,
            "node_times": {**state.get("node_times", {}), "logical_detector": time.time() - start_time},
        }
        
    except Exception as e:
        signal = _create_default_signal()
        return {
            "logical_signal": signal,
            "errors": state.get("errors", []) + [{"node": "logical_detector", "error": str(e)}],
            "node_times": {**state.get("node_times", {}), "logical_detector": time.time() - start_time},
        }


def _create_default_signal() -> FailureSignal:
    """Create a default (no failure) signal."""
    return FailureSignal(
        failure_type="logical_inconsistency",
        detected=False,
        confidence=0.0,
        severity="low",
        evidence=[],
        related_claim_ids=[],
        explanation="Unable to analyze for logical inconsistencies.",
        findings=[],
    )

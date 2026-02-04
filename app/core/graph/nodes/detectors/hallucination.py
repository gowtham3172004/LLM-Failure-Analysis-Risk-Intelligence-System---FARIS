"""
FARIS Hallucination Detector

Detects unsupported factual claims, fabricated information,
and statements not grounded in the provided context.
"""

import time
from typing import Any

from app.core.graph.state import AnalysisState, FailureSignal
from app.core.llm import get_llm_client, PromptTemplates


async def hallucination_detector(state: AnalysisState) -> dict[str, Any]:
    """
    Detect hallucinations in the LLM answer.
    
    Checks for:
    - Claims not supported by provided context
    - Fabricated facts, numbers, or citations
    - Made-up entities, people, or events
    - Incorrect technical details
    
    Args:
        state: Current analysis state
    
    Returns:
        Updated state with hallucination_signal
    """
    start_time = time.time()
    
    question = state.get("question", "")
    context = state.get("context", "") or "No context provided."
    claims = state.get("claims", [])
    
    # Format claims for the prompt
    claims_text = "\n".join([
        f"- [{c['claim_id']}] {c['claim_text']}"
        for c in claims
    ]) if claims else "No claims extracted."
    
    try:
        llm = get_llm_client()
        
        prompt = PromptTemplates.DETECT_HALLUCINATION.format(
            question=question,
            context=context,
            claims=claims_text,
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
                "hallucination_signal": signal,
                "node_times": {**state.get("node_times", {}), "hallucination_detector": time.time() - start_time},
            }
        
        # Extract related claim IDs from findings
        related_claims = []
        findings = result.get("findings", [])
        for finding in findings:
            if finding.get("is_hallucinated", False):
                claim_id = finding.get("claim_id", "")
                if claim_id:
                    related_claims.append(claim_id)
        
        # Build evidence list
        evidence = []
        for finding in findings:
            if finding.get("is_hallucinated", False):
                reason = finding.get("reason", "")
                if reason:
                    evidence.append(reason)
        
        signal = FailureSignal(
            failure_type="hallucination",
            detected=result.get("hallucination_detected", False),
            confidence=result.get("confidence", 0.0),
            severity=result.get("severity", "medium"),
            evidence=evidence,
            related_claim_ids=related_claims,
            explanation=result.get("summary", "No hallucination issues detected."),
            findings=findings,
        )
        
        return {
            "hallucination_signal": signal,
            "node_times": {**state.get("node_times", {}), "hallucination_detector": time.time() - start_time},
        }
        
    except Exception as e:
        signal = _create_default_signal()
        return {
            "hallucination_signal": signal,
            "errors": state.get("errors", []) + [{"node": "hallucination_detector", "error": str(e)}],
            "node_times": {**state.get("node_times", {}), "hallucination_detector": time.time() - start_time},
        }


def _create_default_signal() -> FailureSignal:
    """Create a default (no failure) signal."""
    return FailureSignal(
        failure_type="hallucination",
        detected=False,
        confidence=0.0,
        severity="low",
        evidence=[],
        related_claim_ids=[],
        explanation="Unable to analyze for hallucinations.",
        findings=[],
    )

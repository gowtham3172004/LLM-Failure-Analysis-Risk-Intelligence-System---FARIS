"""
FARIS Overconfidence Detector

Detects unjustified certainty and lack of appropriate hedging.
"""

import time
from typing import Any

from app.core.graph.state import AnalysisState, FailureSignal
from app.core.llm import get_llm_client, PromptTemplates


async def overconfidence_detector(state: AnalysisState) -> dict[str, Any]:
    """
    Detect overconfidence in the LLM answer.
    
    Checks for:
    - Absolute language (always, never, definitely)
    - Lack of uncertainty acknowledgment
    - Definitive statements on uncertain topics
    - Missing caveats or qualifications
    - Tone vs. evidence mismatch
    
    Args:
        state: Current analysis state
    
    Returns:
        Updated state with overconfidence_signal
    """
    start_time = time.time()
    
    question = state.get("question", "")
    answer = state.get("answer", "")
    claims = state.get("claims", [])
    
    # Format claims
    claims_text = "\n".join([
        f"- [{c['claim_id']}] {c['claim_text']}"
        for c in claims
    ]) if claims else "No claims extracted."
    
    try:
        llm = get_llm_client()
        
        prompt = PromptTemplates.DETECT_OVERCONFIDENCE.format(
            question=question,
            answer=answer,
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
                "overconfidence_signal": signal,
                "node_times": {**state.get("node_times", {}), "overconfidence_detector": time.time() - start_time},
            }
        
        # Extract evidence and related claims
        findings = result.get("findings", [])
        related_claims = []
        evidence = []
        
        for finding in findings:
            claim_id = finding.get("claim_id", "")
            if claim_id:
                related_claims.append(claim_id)
            
            text = finding.get("text", "")
            issue = finding.get("issue", "")
            if text and issue:
                evidence.append(f'"{text}" - {issue}')
        
        # Add absolute terms found
        absolute_terms = result.get("absolute_terms_found", [])
        if absolute_terms:
            evidence.append(f"Absolute terms used: {', '.join(absolute_terms)}")
        
        signal = FailureSignal(
            failure_type="overconfidence",
            detected=result.get("overconfidence_detected", False),
            confidence=result.get("confidence", 0.0),
            severity=result.get("severity", "medium"),
            evidence=evidence,
            related_claim_ids=list(set(related_claims)),
            explanation=result.get("summary", "No overconfidence detected."),
            findings=findings,
        )
        
        return {
            "overconfidence_signal": signal,
            "node_times": {**state.get("node_times", {}), "overconfidence_detector": time.time() - start_time},
        }
        
    except Exception as e:
        signal = _create_default_signal()
        return {
            "overconfidence_signal": signal,
            "errors": state.get("errors", []) + [{"node": "overconfidence_detector", "error": str(e)}],
            "node_times": {**state.get("node_times", {}), "overconfidence_detector": time.time() - start_time},
        }


def _create_default_signal() -> FailureSignal:
    """Create a default (no failure) signal."""
    return FailureSignal(
        failure_type="overconfidence",
        detected=False,
        confidence=0.0,
        severity="low",
        evidence=[],
        related_claim_ids=[],
        explanation="Unable to analyze for overconfidence.",
        findings=[],
    )

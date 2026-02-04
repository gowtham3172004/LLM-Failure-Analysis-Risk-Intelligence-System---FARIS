"""
FARIS Explanation Node

Generates human-readable explanations of the analysis results.
"""

import time
from typing import Any

from app.core.graph.state import AnalysisState
from app.core.llm import get_llm_client, PromptTemplates


async def explanation_node(state: AnalysisState) -> dict[str, Any]:
    """
    Generate comprehensive explanation of analysis results.
    
    Creates:
    - Executive summary
    - Key findings list
    - Detailed explanation
    - Impact assessment
    
    Args:
        state: Current analysis state
    
    Returns:
        Updated state with explanation fields
    """
    start_time = time.time()
    
    detected_failures = state.get("detected_failures", [])
    claims = state.get("claims", [])
    risk_score = state.get("risk_score", 0.0)
    risk_level = state.get("risk_level", "low")
    question = state.get("question", "")
    answer = state.get("answer", "")
    
    # If no failures, generate simple explanation
    if not detected_failures:
        explanation = _generate_no_failure_explanation(risk_score, risk_level)
        return {
            "explanation_summary": explanation,
            "key_findings": ["No significant issues detected"],
            "detailed_explanation": explanation,
            "impact_assessment": "Low impact - output appears reliable.",
            "explanation": explanation,
            "node_times": {**state.get("node_times", {}), "explanation": time.time() - start_time},
        }
    
    # Format failures for prompt
    failures_text = "\n".join([
        f"- Type: {f['failure_type']}, Confidence: {f['confidence']:.0%}, "
        f"Severity: {f['severity']}\n  Evidence: {'; '.join(f.get('evidence', [])[:3])}"
        for f in detected_failures
    ])
    
    # Format claims
    claims_text = "\n".join([
        f"- [{c['claim_id']}] {c['claim_text'][:100]}..."
        for c in claims[:10]
    ]) if claims else "No claims extracted."
    
    try:
        llm = get_llm_client()
        
        prompt = PromptTemplates.GENERATE_EXPLANATION.format(
            question=question[:500],
            answer=answer[:1000],
            failures=failures_text,
            claims=claims_text,
            risk_score=f"{risk_score:.2f}",
            risk_level=risk_level.upper(),
        )
        
        result = await llm.generate_structured(
            prompt=prompt,
            system=PromptTemplates.ANALYZER_SYSTEM,
            temperature=0.3,
            max_tokens=1536,
        )
        
        # Handle parsing errors
        if result.get("_parse_error"):
            explanation = _generate_fallback_explanation(
                detected_failures, risk_score, risk_level
            )
            return {
                "explanation_summary": explanation,
                "key_findings": [f["failure_type"] for f in detected_failures],
                "detailed_explanation": explanation,
                "impact_assessment": f"Risk level: {risk_level}",
                "explanation": explanation,
                "node_times": {**state.get("node_times", {}), "explanation": time.time() - start_time},
            }
        
        summary = result.get("summary", "Analysis complete.")
        key_findings = result.get("key_findings", [])
        detailed = result.get("detailed_explanation", summary)
        impact = result.get("impact_assessment", "")
        
        # Combine into final explanation
        final_explanation = f"{summary}\n\n{detailed}"
        if impact:
            final_explanation += f"\n\nImpact: {impact}"
        
        return {
            "explanation_summary": summary,
            "key_findings": key_findings,
            "detailed_explanation": detailed,
            "impact_assessment": impact,
            "explanation": final_explanation,
            "node_times": {**state.get("node_times", {}), "explanation": time.time() - start_time},
        }
        
    except Exception as e:
        explanation = _generate_fallback_explanation(
            detected_failures, risk_score, risk_level
        )
        return {
            "explanation_summary": explanation,
            "key_findings": [f["failure_type"] for f in detected_failures],
            "detailed_explanation": explanation,
            "impact_assessment": f"Risk level: {risk_level}",
            "explanation": explanation,
            "errors": state.get("errors", []) + [{"node": "explanation", "error": str(e)}],
            "node_times": {**state.get("node_times", {}), "explanation": time.time() - start_time},
        }


def _generate_no_failure_explanation(risk_score: float, risk_level: str) -> str:
    """Generate explanation when no failures detected."""
    return (
        f"The analysis found no significant reliability issues with this LLM output. "
        f"Risk score: {risk_score:.2f} ({risk_level}). "
        "The response appears to be appropriate for the given question and context. "
        "Standard deployment practices are recommended."
    )


def _generate_fallback_explanation(
    detected_failures: list,
    risk_score: float,
    risk_level: str,
) -> str:
    """Generate a basic explanation without LLM."""
    failure_types = [f["failure_type"].replace("_", " ").title() for f in detected_failures]
    failure_list = ", ".join(failure_types)
    
    return (
        f"Analysis detected {len(detected_failures)} potential issue(s): {failure_list}. "
        f"Overall risk score: {risk_score:.2f} ({risk_level.upper()}). "
        "Review the detailed findings and evidence for each failure type. "
        "Consider the recommendations provided to mitigate these issues."
    )

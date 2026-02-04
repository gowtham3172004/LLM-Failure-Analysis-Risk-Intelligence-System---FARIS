"""
FARIS Recommendation Node

Generates actionable recommendations based on detected failures.
"""

import time
from typing import Any

from app.core.graph.state import AnalysisState, RecommendationData
from app.core.llm import get_llm_client, PromptTemplates


# Predefined recommendations for each failure type
RECOMMENDATIONS_DB = {
    "hallucination": [
        {
            "title": "Implement RAG with verified sources",
            "description": "Add retrieval-augmented generation to ground responses in verified documents.",
            "implementation_hint": "Use vector databases like ChromaDB/Pinecone with curated knowledge bases.",
            "priority": 1,
        },
        {
            "title": "Add source citations requirement",
            "description": "Require the LLM to cite sources for factual claims.",
            "implementation_hint": "Include citation requirements in the system prompt.",
            "priority": 2,
        },
        {
            "title": "Implement fact-checking pipeline",
            "description": "Add a post-processing step to verify factual claims.",
            "implementation_hint": "Use a separate verification model or knowledge graph queries.",
            "priority": 2,
        },
    ],
    "logical_inconsistency": [
        {
            "title": "Add chain-of-thought prompting",
            "description": "Require the model to show reasoning steps explicitly.",
            "implementation_hint": "Use 'Let's think step by step' or similar CoT triggers.",
            "priority": 1,
        },
        {
            "title": "Implement self-consistency checking",
            "description": "Generate multiple responses and check for consistency.",
            "implementation_hint": "Sample 3-5 responses and look for agreement.",
            "priority": 2,
        },
        {
            "title": "Add logical validation layer",
            "description": "Use a separate model to validate logical consistency.",
            "implementation_hint": "Implement a critic model that checks reasoning chains.",
            "priority": 3,
        },
    ],
    "missing_assumptions": [
        {
            "title": "Require explicit assumption listing",
            "description": "Prompt the model to list all assumptions before answering.",
            "implementation_hint": "Add 'First, list your assumptions:' to the prompt structure.",
            "priority": 1,
        },
        {
            "title": "Implement clarification requests",
            "description": "Allow the model to ask clarifying questions when information is missing.",
            "implementation_hint": "Add logic to detect and handle clarification requests.",
            "priority": 2,
        },
        {
            "title": "Provide comprehensive context",
            "description": "Ensure all necessary context is included in the prompt.",
            "implementation_hint": "Create context templates that capture required information.",
            "priority": 2,
        },
    ],
    "overconfidence": [
        {
            "title": "Request confidence qualifiers",
            "description": "Ask the model to express uncertainty when appropriate.",
            "implementation_hint": "Add 'Express your confidence level' to prompts.",
            "priority": 1,
        },
        {
            "title": "Implement calibration training",
            "description": "Fine-tune or prompt-engineer for better calibrated confidence.",
            "implementation_hint": "Use examples that demonstrate appropriate hedging.",
            "priority": 2,
        },
        {
            "title": "Post-process absolute statements",
            "description": "Add filters to catch and flag absolute language.",
            "implementation_hint": "Use regex or NLP to detect 'always', 'never', etc.",
            "priority": 3,
        },
    ],
    "scope_violation": [
        {
            "title": "Add scope constraints to prompts",
            "description": "Explicitly define the scope of acceptable responses.",
            "implementation_hint": "Include 'Only answer the specific question asked' in system prompt.",
            "priority": 1,
        },
        {
            "title": "Implement response filtering",
            "description": "Filter out tangential information from responses.",
            "implementation_hint": "Use a summarization step focused on the original question.",
            "priority": 2,
        },
    ],
    "underspecification": [
        {
            "title": "Implement ambiguity detection",
            "description": "Detect ambiguous queries before processing.",
            "implementation_hint": "Use a classifier to identify underspecified questions.",
            "priority": 1,
        },
        {
            "title": "Add clarification workflow",
            "description": "Implement a multi-turn clarification process.",
            "implementation_hint": "Create a dialogue system for gathering missing information.",
            "priority": 2,
        },
        {
            "title": "Provide default assumptions",
            "description": "Define and communicate standard assumptions when info is missing.",
            "implementation_hint": "Create domain-specific default assumption sets.",
            "priority": 3,
        },
    ],
}


async def recommendation_node(state: AnalysisState) -> dict[str, Any]:
    """
    Generate actionable recommendations for detected failures.
    
    Maps each detected failure type to specific, actionable recommendations
    that developers can implement.
    
    Args:
        state: Current analysis state
    
    Returns:
        Updated state with recommendations
    """
    start_time = time.time()
    
    detected_failures = state.get("detected_failures", [])
    domain = state.get("domain", "general")
    
    if not detected_failures:
        return {
            "recommendations": [],
            "node_times": {**state.get("node_times", {}), "recommendation": time.time() - start_time},
        }
    
    recommendations: list[RecommendationData] = []
    rec_id_counter = 1
    
    # Get unique failure types, sorted by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    sorted_failures = sorted(
        detected_failures,
        key=lambda x: severity_order.get(x.get("severity", "medium"), 2),
    )
    
    seen_types = set()
    
    for failure in sorted_failures:
        failure_type = failure.get("failure_type", "")
        
        if failure_type in seen_types:
            continue
        seen_types.add(failure_type)
        
        # Get predefined recommendations for this failure type
        type_recs = RECOMMENDATIONS_DB.get(failure_type, [])
        
        # Add recommendations (top 2 per failure type)
        for rec in type_recs[:2]:
            recommendations.append(RecommendationData(
                recommendation_id=f"r{rec_id_counter}",
                priority=rec["priority"],
                failure_type=failure_type,
                title=rec["title"],
                description=rec["description"],
                implementation_hint=rec.get("implementation_hint"),
            ))
            rec_id_counter += 1
    
    # Sort by priority
    recommendations.sort(key=lambda x: x["priority"])
    
    # Optionally, use LLM for domain-specific recommendations
    if domain != "general" and detected_failures:
        try:
            domain_recs = await _generate_domain_recommendations(
                detected_failures, domain
            )
            recommendations.extend(domain_recs)
        except Exception:
            pass  # Fallback to predefined only
    
    # Limit total recommendations
    recommendations = recommendations[:10]
    
    return {
        "recommendations": recommendations,
        "node_times": {**state.get("node_times", {}), "recommendation": time.time() - start_time},
    }


async def _generate_domain_recommendations(
    detected_failures: list,
    domain: str,
) -> list[RecommendationData]:
    """
    Generate domain-specific recommendations using LLM.
    
    Args:
        detected_failures: List of detected failures
        domain: The analysis domain
    
    Returns:
        List of domain-specific recommendations
    """
    llm = get_llm_client()
    
    failures_text = "\n".join([
        f"- {f['failure_type']}: {f.get('explanation', '')[:100]}"
        for f in detected_failures
    ])
    
    prompt = PromptTemplates.GENERATE_RECOMMENDATIONS.format(
        failures=failures_text,
        domain=domain,
    )
    
    result = await llm.generate_structured(
        prompt=prompt,
        system=PromptTemplates.ANALYZER_SYSTEM,
        temperature=0.3,
        max_tokens=1024,
    )
    
    if result.get("_parse_error"):
        return []
    
    recommendations = []
    raw_recs = result.get("recommendations", [])
    
    for rec in raw_recs[:3]:  # Limit domain-specific recs
        recommendations.append(RecommendationData(
            recommendation_id=rec.get("recommendation_id", "rd1"),
            priority=rec.get("priority", 3),
            failure_type=rec.get("failure_type", "general"),
            title=rec.get("title", "Domain-specific recommendation"),
            description=rec.get("description", ""),
            implementation_hint=rec.get("implementation_hint"),
        ))
    
    return recommendations

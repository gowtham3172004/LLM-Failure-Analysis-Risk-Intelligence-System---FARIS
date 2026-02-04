"""
FARIS Decomposition Node

Breaks down LLM answers into atomic claims, assumptions, and reasoning steps.
This is critical for precise failure detection.
"""

import time
from typing import Any

from app.core.graph.state import AnalysisState, ClaimData
from app.core.llm import get_llm_client, PromptTemplates


async def decomposition_node(state: AnalysisState) -> dict[str, Any]:
    """
    Decompose the LLM answer into analyzable components.
    
    This node extracts:
    1. Atomic claims - individual statements of fact/opinion
    2. Assumptions - implicit and explicit premises
    3. Reasoning steps - logical flow if present
    
    Args:
        state: Current analysis state
    
    Returns:
        Updated state with claims, assumptions, and reasoning_steps
    """
    start_time = time.time()
    
    question = state.get("question", "")
    answer = state.get("answer", "")
    context = state.get("context", "") or "No additional context provided."
    
    try:
        llm = get_llm_client()
        
        prompt = PromptTemplates.DECOMPOSE_CLAIMS.format(
            question=question,
            answer=answer,
            context=context,
        )
        
        result = await llm.generate_structured(
            prompt=prompt,
            system=PromptTemplates.ANALYZER_SYSTEM,
            temperature=0.1,
            max_tokens=2048,
        )
        
        # Handle parsing errors
        if result.get("_parse_error"):
            # Create basic claims from sentences
            claims = _fallback_claim_extraction(answer)
            return {
                "claims": claims,
                "assumptions": [],
                "reasoning_steps": [],
                "errors": state.get("errors", []) + [
                    {"node": "decomposition", "error": "LLM output parsing failed, using fallback"}
                ],
                "node_times": {**state.get("node_times", {}), "decomposition": time.time() - start_time},
            }
        
        # Extract claims
        raw_claims = result.get("claims", [])
        claims: list[ClaimData] = []
        
        for i, claim in enumerate(raw_claims):
            claims.append(ClaimData(
                claim_id=claim.get("claim_id", f"c{i+1}"),
                claim_text=claim.get("claim_text", ""),
                claim_type=claim.get("claim_type", "factual"),
                implicit_assumptions=claim.get("implicit_assumptions", []),
            ))
        
        # If no claims extracted, use fallback
        if not claims:
            claims = _fallback_claim_extraction(answer)
        
        # Extract assumptions
        assumptions = result.get("overall_assumptions", [])
        
        # Add claim-level assumptions
        for claim in claims:
            assumptions.extend(claim.get("implicit_assumptions", []))
        
        # Deduplicate assumptions
        assumptions = list(set(assumptions))
        
        # Extract reasoning chain
        reasoning_steps = result.get("reasoning_chain", [])
        
        return {
            "claims": claims,
            "assumptions": assumptions,
            "reasoning_steps": reasoning_steps,
            "node_times": {**state.get("node_times", {}), "decomposition": time.time() - start_time},
        }
        
    except Exception as e:
        # Fallback to basic extraction
        claims = _fallback_claim_extraction(answer)
        
        return {
            "claims": claims,
            "assumptions": [],
            "reasoning_steps": [],
            "errors": state.get("errors", []) + [{"node": "decomposition", "error": str(e)}],
            "node_times": {**state.get("node_times", {}), "decomposition": time.time() - start_time},
        }


def _fallback_claim_extraction(answer: str) -> list[ClaimData]:
    """
    Simple fallback claim extraction based on sentences.
    
    Used when LLM-based extraction fails.
    
    Args:
        answer: The answer text
    
    Returns:
        List of basic ClaimData
    """
    import re
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', answer.strip())
    
    claims = []
    for i, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if len(sentence) > 10:  # Skip very short fragments
            claims.append(ClaimData(
                claim_id=f"c{i+1}",
                claim_text=sentence,
                claim_type="factual",
                implicit_assumptions=[],
            ))
    
    return claims[:20]  # Limit to prevent explosion

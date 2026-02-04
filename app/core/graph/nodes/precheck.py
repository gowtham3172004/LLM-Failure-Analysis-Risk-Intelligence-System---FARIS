"""
FARIS Precheck Node

Validates input quality before expensive analysis.
Filters out invalid, empty, or unsuitable inputs early.
"""

import time
from typing import Any

from app.core.graph.state import AnalysisState
from app.core.llm import get_llm_client, PromptTemplates


async def precheck_node(state: AnalysisState) -> dict[str, Any]:
    """
    Validate input before analysis.
    
    This node:
    1. Checks for empty/trivial inputs
    2. Identifies refusal responses
    3. Detects error messages
    4. Validates content is analyzable
    
    Args:
        state: Current analysis state
    
    Returns:
        Updated state fields
    """
    start_time = time.time()
    
    question = state.get("question", "").strip()
    answer = state.get("answer", "").strip()
    
    # Quick validation checks
    if not question:
        return {
            "precheck_passed": False,
            "precheck_failure_reason": "Question is empty",
            "answer_type": "invalid",
            "node_times": {**state.get("node_times", {}), "precheck": time.time() - start_time},
        }
    
    if not answer:
        return {
            "precheck_passed": False,
            "precheck_failure_reason": "Answer is empty",
            "answer_type": "empty",
            "node_times": {**state.get("node_times", {}), "precheck": time.time() - start_time},
        }
    
    # Check for obvious refusal patterns
    refusal_patterns = [
        "i cannot",
        "i can't",
        "i'm not able to",
        "i am not able to",
        "i don't have access",
        "i'm sorry, but i cannot",
        "as an ai",
        "i'm unable to",
    ]
    
    answer_lower = answer.lower()
    is_refusal = any(pattern in answer_lower for pattern in refusal_patterns)
    
    if is_refusal and len(answer) < 200:  # Short refusals
        return {
            "precheck_passed": True,  # Still analyze refusals, but mark them
            "precheck_failure_reason": None,
            "answer_type": "refusal",
            "node_times": {**state.get("node_times", {}), "precheck": time.time() - start_time},
        }
    
    # Check for error patterns
    error_patterns = [
        "error:",
        "exception:",
        "traceback",
        "failed to",
        "unable to process",
    ]
    
    is_error = any(pattern in answer_lower for pattern in error_patterns)
    
    if is_error and len(answer) < 500:
        return {
            "precheck_passed": False,
            "precheck_failure_reason": "Answer appears to be an error message",
            "answer_type": "error",
            "node_times": {**state.get("node_times", {}), "precheck": time.time() - start_time},
        }
    
    # For more complex validation, use LLM
    try:
        llm = get_llm_client()
        
        prompt = PromptTemplates.PRECHECK_INPUT.format(
            question=question[:1000],  # Limit for efficiency
            answer=answer[:2000],
        )
        
        result = await llm.generate_structured(
            prompt=prompt,
            system=PromptTemplates.ANALYZER_SYSTEM,
            temperature=0.1,
            max_tokens=512,
        )
        
        # Handle parsing errors
        if result.get("_parse_error"):
            # Default to passing if we can't parse
            return {
                "precheck_passed": True,
                "precheck_failure_reason": None,
                "answer_type": "response",
                "node_times": {**state.get("node_times", {}), "precheck": time.time() - start_time},
            }
        
        is_valid = result.get("is_valid", True)
        answer_type = result.get("answer_type", "response")
        proceed = result.get("proceed_with_analysis", True)
        
        return {
            "precheck_passed": is_valid and proceed,
            "precheck_failure_reason": result.get("reason") if not (is_valid and proceed) else None,
            "answer_type": answer_type,
            "node_times": {**state.get("node_times", {}), "precheck": time.time() - start_time},
        }
        
    except Exception as e:
        # On error, default to passing (don't block analysis)
        return {
            "precheck_passed": True,
            "precheck_failure_reason": None,
            "answer_type": "response",
            "errors": state.get("errors", []) + [{"node": "precheck", "error": str(e)}],
            "node_times": {**state.get("node_times", {}), "precheck": time.time() - start_time},
        }

"""
FARIS Precheck Node

Validates input quality before analysis — purely pattern-based,
NO LLM call required.  This keeps the total pipeline at 1-2 LLM
calls instead of wasting one on input validation.
"""

import time
from typing import Any

from app.core.graph.state import AnalysisState


async def precheck_node(state: AnalysisState) -> dict[str, Any]:
    """
    Validate input before analysis using fast pattern matching.

    Checks:
    1. Empty / trivial inputs
    2. Refusal patterns
    3. Error message patterns

    Returns:
        Updated precheck state fields.
    """
    start_time = time.time()

    question = state.get("question", "").strip()
    answer = state.get("answer", "").strip()

    # --- Empty checks ---
    if not question:
        return _fail(state, start_time, "Question is empty", "invalid")
    if not answer:
        return _fail(state, start_time, "Answer is empty", "empty")

    # --- Refusal patterns ---
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
    is_refusal = any(p in answer_lower for p in refusal_patterns)

    if is_refusal and len(answer) < 200:
        return _pass(state, start_time, "refusal")

    # --- Error patterns ---
    error_patterns = [
        "error:",
        "exception:",
        "traceback",
        "failed to",
        "unable to process",
    ]
    is_error = any(p in answer_lower for p in error_patterns)
    if is_error and len(answer) < 500:
        return _fail(state, start_time, "Answer appears to be an error message", "error")

    # --- Default: pass ---
    return _pass(state, start_time, "response")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _pass(state: AnalysisState, start: float, answer_type: str) -> dict[str, Any]:
    return {
        "precheck_passed": True,
        "precheck_failure_reason": None,
        "answer_type": answer_type,
        "node_times": {**state.get("node_times", {}), "precheck": time.time() - start},
    }


def _fail(state: AnalysisState, start: float, reason: str, answer_type: str) -> dict[str, Any]:
    return {
        "precheck_passed": False,
        "precheck_failure_reason": reason,
        "answer_type": answer_type,
        "node_times": {**state.get("node_times", {}), "precheck": time.time() - start},
    }

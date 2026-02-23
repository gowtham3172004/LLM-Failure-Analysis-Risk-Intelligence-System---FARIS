"""
FARIS Remediation Node — The Self-Healing Loop

If a failure is detected and the risk_score exceeds the threshold,
this node calls the LLM with the *verified* context and the failure
report to rewrite the answer so it is strictly grounded in truth.

The remediated answer is stored in the state and returned as part
of the API response.
"""

import time
from typing import Any

import structlog

from app.core.graph.state import AnalysisState
from app.core.llm import get_llm_client

logger = structlog.get_logger()

# Risk score threshold above which remediation is triggered
REMEDIATION_THRESHOLD = 0.3


def _build_failure_summary(state: AnalysisState) -> str:
    """Build a concise failure summary for the remediation prompt."""
    lines: list[str] = []
    for f in state.get("detected_failures", []):
        if f.get("detected"):
            lines.append(
                f"- [{f.get('failure_type', 'unknown').upper()}] "
                f"(confidence={f.get('confidence', 0):.0%}, severity={f.get('severity', 'unknown')}): "
                f"{f.get('explanation', 'No explanation')}"
            )
    return "\n".join(lines) if lines else "No specific failures documented."


async def remediation_node(state: AnalysisState) -> dict[str, Any]:
    """
    Generate a corrected answer when failures are detected.

    Condition: only fires when risk_score > REMEDIATION_THRESHOLD.

    The LLM is prompted as a "Truth Correction Engine" and MUST
    base the rewrite strictly on the verified_context. If no
    verified context is available it falls back to the original
    context field.

    Args:
        state: Current pipeline state.

    Returns:
        Dict with remediation fields.
    """
    start = time.time()
    risk_score = state.get("risk_score", 0.0)

    if risk_score <= REMEDIATION_THRESHOLD:
        logger.info(
            "remediation.skipped",
            risk_score=risk_score,
            reason="below threshold",
        )
        return {
            "remediation_attempted": False,
            "remediated_answer": None,
            "remediation_explanation": None,
            "node_times": {
                **state.get("node_times", {}),
                "remediation": time.time() - start,
            },
        }

    # Use verified (refined) context first, fall back to the raw context
    context = state.get("verified_context") or state.get("context") or ""
    question = state.get("question", "")
    original_answer = state.get("answer", "")
    failure_summary = _build_failure_summary(state)

    system_prompt = (
        "You are a Truth Correction Engine for the FARIS system. "
        "Your ONLY job is to rewrite the given answer so that it is "
        "100% accurate, based STRICTLY on the provided context. "
        "Rules:\n"
        "1. Never invent facts. If the context does not contain the "
        "   information, explicitly say 'The provided context does not "
        "   contain this information.'\n"
        "2. Preserve the original question's intent.\n"
        "3. Fix every failure identified in the failure report.\n"
        "4. Use hedging language where certainty cannot be established.\n"
        "5. Keep the tone professional and concise."
    )

    user_prompt = (
        f"### ORIGINAL QUESTION\n{question}\n\n"
        f"### ORIGINAL ANSWER (contains failures)\n{original_answer}\n\n"
        f"### FAILURE REPORT\n{failure_summary}\n\n"
        f"### VERIFIED CONTEXT (ground truth)\n{context[:6000]}\n\n"
        "### TASK\n"
        "Rewrite the answer to be accurate based strictly on the "
        "verified context. Fix all identified failures."
    )

    try:
        llm = get_llm_client()
        remediated = await llm.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.15,
            max_tokens=2048,
        )

        explanation = (
            f"Risk score ({risk_score:.2f}) exceeded the "
            f"remediation threshold ({REMEDIATION_THRESHOLD}). "
            f"The answer was rewritten using verified context to address "
            f"{len(state.get('detected_failures', []))} detected failure(s)."
        )

        logger.info(
            "remediation.success",
            risk_score=risk_score,
            original_len=len(original_answer),
            remediated_len=len(remediated),
        )

        return {
            "remediation_attempted": True,
            "remediated_answer": remediated.strip(),
            "remediation_explanation": explanation,
            "node_times": {
                **state.get("node_times", {}),
                "remediation": time.time() - start,
            },
        }

    except Exception as exc:
        logger.error("remediation.failed", error=str(exc))
        return {
            "remediation_attempted": True,
            "remediated_answer": None,
            "remediation_explanation": f"Remediation failed: {exc}",
            "errors": [
                *state.get("errors", []),
                {"node": "remediation", "error": str(exc)},
            ],
            "node_times": {
                **state.get("node_times", {}),
                "remediation": time.time() - start,
            },
        }

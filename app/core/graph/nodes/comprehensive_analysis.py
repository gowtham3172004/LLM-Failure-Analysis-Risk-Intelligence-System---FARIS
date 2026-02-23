"""
FARIS Comprehensive Analysis Node

Single-call analysis that performs claim decomposition AND all six
failure detections in ONE LLM call. This eliminates the 12+ call
problem that caused rate-limit exhaustion and silent failures.

Output is parsed into the same state fields the rest of the pipeline
expects (claims, individual detector signals, etc.) so downstream
nodes (aggregation, risk_scoring, recommendation, remediation)
continue to work unchanged.
"""

import time
from typing import Any

import structlog

from app.core.graph.state import AnalysisState, ClaimData, FailureSignal
from app.core.llm import get_llm_client

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# The single comprehensive prompt
# ---------------------------------------------------------------------------
COMPREHENSIVE_SYSTEM = (
    "You are FARIS, an expert AI failure-analysis system. "
    "Your job is to rigorously analyze an LLM-generated answer for ALL "
    "possible reliability issues. You MUST be aggressive about finding "
    "real problems — missing a genuine failure is far worse than a false "
    "positive. If a factual claim is wrong, you MUST flag it. "
    "Always respond with valid JSON in the exact format requested."
)

COMPREHENSIVE_PROMPT = """You are analyzing an LLM's answer for reliability failures.

=== INPUT ===
QUESTION: {question}

LLM ANSWER TO ANALYZE: {answer}

REFERENCE CONTEXT (ground truth — if provided): {context}

DOMAIN: {domain}

=== YOUR TASK ===
Perform a COMPLETE failure analysis. You must:

1. **DECOMPOSE** the answer into individual atomic claims.
2. **DETECT** all six failure types below for EACH claim and overall:

   a) **HALLUCINATION** — Fabricated facts, wrong information, claims not
      supported by the context or known reality. If the answer states
      something factually incorrect (e.g., wrong capital city, wrong
      version number, non-existent features), this is hallucination.
      BE AGGRESSIVE: if a factual claim contradicts well-known facts
      or the provided context, mark it as hallucinated with HIGH confidence.

   b) **LOGICAL INCONSISTENCY** — Contradictions, non sequiturs, invalid
      reasoning, circular arguments within the answer.

   c) **MISSING ASSUMPTIONS** — Critical unstated assumptions that the
      answer depends on but never acknowledges.

   d) **OVERCONFIDENCE** — Unjustified certainty, absolute language
      ("always", "never", "definitely") without sufficient evidence,
      presenting uncertain claims as definitive facts.

   e) **SCOPE VIOLATION** — Answer goes beyond what was asked, introduces
      tangential topics, or provides unsolicited information.

   f) **UNDERSPECIFICATION** — The question was ambiguous or lacked
      information, and the answer should have asked for clarification
      or acknowledged the ambiguity but didn't.

3. **EXPLAIN** the key findings in plain language.

=== CRITICAL RULES ===
- If the answer contains a WRONG FACT, you MUST detect it as hallucination
  with confidence >= 0.9 and severity "high" or "critical".
- Compare claims against the reference context AND your own knowledge.
- "No context provided" does NOT mean you can't detect errors — use your
  own knowledge of facts to identify hallucinations.
- For each detected failure, provide SPECIFIC evidence from the answer.
- Be thorough: analyze EVERY claim, not just the first one.

=== RESPOND WITH THIS EXACT JSON STRUCTURE ===
{{
    "claims": [
        {{
            "claim_id": "c1",
            "claim_text": "The specific claim extracted from the answer",
            "claim_type": "factual|opinion|reasoning",
            "is_correct": true or false,
            "correction": "The correct information if claim is wrong, null if correct"
        }}
    ],

    "failures": {{
        "hallucination": {{
            "detected": true or false,
            "confidence": 0.0 to 1.0,
            "severity": "low|medium|high|critical",
            "evidence": ["specific evidence string 1", "specific evidence string 2"],
            "explanation": "Summary of hallucination findings",
            "related_claim_ids": ["c1", "c2"]
        }},
        "logical_inconsistency": {{
            "detected": true or false,
            "confidence": 0.0 to 1.0,
            "severity": "low|medium|high|critical",
            "evidence": ["evidence"],
            "explanation": "Summary",
            "related_claim_ids": []
        }},
        "missing_assumptions": {{
            "detected": true or false,
            "confidence": 0.0 to 1.0,
            "severity": "low|medium|high|critical",
            "evidence": ["evidence"],
            "explanation": "Summary",
            "related_claim_ids": []
        }},
        "overconfidence": {{
            "detected": true or false,
            "confidence": 0.0 to 1.0,
            "severity": "low|medium|high|critical",
            "evidence": ["evidence"],
            "explanation": "Summary",
            "related_claim_ids": []
        }},
        "scope_violation": {{
            "detected": true or false,
            "confidence": 0.0 to 1.0,
            "severity": "low|medium|high|critical",
            "evidence": ["evidence"],
            "explanation": "Summary",
            "related_claim_ids": []
        }},
        "underspecification": {{
            "detected": true or false,
            "confidence": 0.0 to 1.0,
            "severity": "low|medium|high|critical",
            "evidence": ["evidence"],
            "explanation": "Summary",
            "related_claim_ids": []
        }}
    }},

    "overall_summary": "A 2-3 sentence summary of all findings",
    "key_findings": ["Finding 1 in plain English", "Finding 2"],
    "impact_assessment": "How these failures could affect users relying on this answer"
}}

Now analyze the LLM answer above. Be thorough and precise."""


# ---------------------------------------------------------------------------
# Helper: build FailureSignal from the parsed dict
# ---------------------------------------------------------------------------
def _to_signal(failure_type: str, data: dict) -> FailureSignal:
    """Convert a parsed failure dict to a FailureSignal."""
    return FailureSignal(
        failure_type=failure_type,
        detected=bool(data.get("detected", False)),
        confidence=float(data.get("confidence", 0.0)),
        severity=data.get("severity", "medium"),
        evidence=data.get("evidence", []),
        related_claim_ids=data.get("related_claim_ids", []),
        explanation=data.get("explanation", f"No {failure_type} issues detected."),
        findings=[],  # compat with old detailed findings
    )


def _default_signal(failure_type: str) -> FailureSignal:
    return FailureSignal(
        failure_type=failure_type,
        detected=False,
        confidence=0.0,
        severity="low",
        evidence=[],
        related_claim_ids=[],
        explanation=f"Unable to analyze for {failure_type}.",
        findings=[],
    )


# ---------------------------------------------------------------------------
# The node
# ---------------------------------------------------------------------------
async def comprehensive_analysis_node(state: AnalysisState) -> dict[str, Any]:
    """
    Single LLM call that performs claim decomposition + all 6 failure
    detections at once.

    Returns state updates compatible with aggregation, risk_scoring,
    explanation, recommendation, and remediation nodes.
    """
    start_time = time.time()

    question = state.get("question", "")
    answer = state.get("answer", "")
    context = state.get("context", "") or "No context provided."
    domain = state.get("domain", "general")

    prompt = COMPREHENSIVE_PROMPT.format(
        question=question,
        answer=answer,
        context=context[:6000],  # cap context length
        domain=domain,
    )

    try:
        llm = get_llm_client()
        result = await llm.generate_structured(
            prompt=prompt,
            system=COMPREHENSIVE_SYSTEM,
            temperature=0.1,
            max_tokens=4096,
        )

        logger.info(
            "comprehensive_analysis.llm_result",
            parse_error=result.get("_parse_error", False),
            keys=list(result.keys()),
        )

        if result.get("_parse_error"):
            # LLM returned something unparseable — this is a real error,
            # NOT a silent pass.  Surface it so the user knows.
            return _error_state(state, start_time, "LLM returned unparseable output")

        # ----- Parse claims -----
        raw_claims = result.get("claims", [])
        claims: list[ClaimData] = []
        for i, c in enumerate(raw_claims):
            claims.append(ClaimData(
                claim_id=c.get("claim_id", f"c{i+1}"),
                claim_text=c.get("claim_text", ""),
                claim_type=c.get("claim_type", "factual"),
                implicit_assumptions=[],
            ))

        if not claims:
            # Fallback: treat whole answer as one claim
            claims = [ClaimData(
                claim_id="c1",
                claim_text=answer[:500],
                claim_type="factual",
                implicit_assumptions=[],
            )]

        # ----- Parse failure signals -----
        failures_block = result.get("failures", {})

        signal_map = {
            "hallucination": "hallucination_signal",
            "logical_inconsistency": "logical_signal",
            "missing_assumptions": "assumptions_signal",
            "overconfidence": "overconfidence_signal",
            "scope_violation": "scope_signal",
            "underspecification": "underspec_signal",
        }

        signals: dict[str, FailureSignal] = {}
        for ftype, state_key in signal_map.items():
            fdata = failures_block.get(ftype, {})
            if fdata:
                signals[state_key] = _to_signal(ftype, fdata)
            else:
                signals[state_key] = _default_signal(ftype)

        # ----- Explanation fields (from the same response) -----
        overall_summary = result.get("overall_summary", "Analysis complete.")
        key_findings = result.get("key_findings", [])
        impact = result.get("impact_assessment", "")

        elapsed = time.time() - start_time
        return {
            # Decomposition results
            "claims": claims,
            "assumptions": [],
            "reasoning_steps": [],
            # Detector signals
            **signals,
            # Explanation fields (pre-filled so explanation_node can be skipped)
            "explanation_summary": overall_summary,
            "key_findings": key_findings,
            "detailed_explanation": overall_summary,
            "impact_assessment": impact,
            "explanation": f"{overall_summary}\n\n{impact}" if impact else overall_summary,
            # Timing
            "node_times": {
                **state.get("node_times", {}),
                "comprehensive_analysis": elapsed,
            },
        }

    except Exception as exc:
        logger.error("comprehensive_analysis.error", error=str(exc), type=type(exc).__name__)
        err_str = str(exc).lower()
        # If it's a rate limit / quota error, re-raise so the API layer
        # can return a proper HTTP 429 instead of fake "no failures" results.
        if any(kw in err_str for kw in ("rate limit", "429", "quota", "ratelimit")):
            raise RuntimeError(
                "Gemini API rate limit exceeded after all retries. "
                "Please wait a few minutes and try again."
            ) from exc
        return _error_state(state, start_time, str(exc))


def _error_state(state: AnalysisState, start_time: float, error_msg: str) -> dict[str, Any]:
    """
    Return an error state that does NOT silently hide the problem.
    Instead of faking 'no failures', we flag the analysis as degraded.
    """
    return {
        "claims": [ClaimData(
            claim_id="c1",
            claim_text=state.get("answer", "")[:500],
            claim_type="factual",
            implicit_assumptions=[],
        )],
        "assumptions": [],
        "reasoning_steps": [],
        # NO fake "detected=False" signals — leave them as None
        # so aggregation knows the detectors never ran
        "hallucination_signal": None,
        "logical_signal": None,
        "assumptions_signal": None,
        "overconfidence_signal": None,
        "scope_signal": None,
        "underspec_signal": None,
        # Explanation reflects the error
        "explanation_summary": f"Analysis could not be completed: {error_msg}",
        "key_findings": ["Analysis failed — please retry"],
        "detailed_explanation": f"The analysis pipeline encountered an error: {error_msg}",
        "impact_assessment": "Results are unavailable due to an error.",
        "explanation": f"Analysis could not be completed: {error_msg}",
        # Record the error
        "errors": state.get("errors", []) + [
            {"node": "comprehensive_analysis", "error": error_msg}
        ],
        "node_times": {
            **state.get("node_times", {}),
            "comprehensive_analysis": time.time() - start_time,
        },
    }

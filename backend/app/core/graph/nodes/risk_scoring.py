"""
FARIS Risk Scoring Node

Calculates a deterministic, explainable risk score based on detected failures.
"""

import time
from typing import Any

from app.config import get_settings
from app.core.graph.state import AnalysisState

settings = get_settings()


async def risk_scoring_node(state: AnalysisState) -> dict[str, Any]:
    """
    Calculate deployment risk score.
    
    Uses a deterministic formula:
    risk = Σ (failure_confidence × severity_weight × domain_multiplier)
    
    The score is normalized to 0-1 and categorized into risk levels.
    
    Args:
        state: Current analysis state
    
    Returns:
        Updated state with risk_score, risk_level, and explanations
    """
    start_time = time.time()
    
    detected_failures = state.get("detected_failures", [])
    domain = state.get("domain", "general")
    
    # Get weights from settings
    failure_weights = settings.failure_weights
    domain_multipliers = settings.domain_multipliers
    
    # Get domain multiplier
    domain_multiplier = domain_multipliers.get(domain, 1.0)
    
    # Severity multipliers
    severity_multipliers = {
        "low": 0.25,
        "medium": 0.5,
        "high": 0.75,
        "critical": 1.0,
    }
    
    # Calculate risk
    total_risk = 0.0
    contributing_factors = []
    
    for failure in detected_failures:
        failure_type = failure.get("failure_type", "")
        confidence = failure.get("confidence", 0.0)
        severity = failure.get("severity", "medium")
        
        # Get weights
        type_weight = failure_weights.get(failure_type, 0.1)
        severity_mult = severity_multipliers.get(severity, 0.5)
        
        # Calculate contribution
        contribution = confidence * type_weight * severity_mult * domain_multiplier
        total_risk += contribution
        
        contributing_factors.append({
            "failure_type": failure_type,
            "confidence": confidence,
            "severity": severity,
            "type_weight": type_weight,
            "severity_multiplier": severity_mult,
            "domain_multiplier": domain_multiplier,
            "contribution": round(contribution, 4),
        })
    
    # Normalize risk score to 0-1
    # Using a soft cap to allow scores to approach but not exceed 1
    risk_score = min(total_risk, 1.0)
    
    # Determine risk level
    if risk_score < 0.25:
        risk_level = "low"
    elif risk_score < 0.5:
        risk_level = "medium"
    elif risk_score < 0.75:
        risk_level = "high"
    else:
        risk_level = "critical"
    
    # Generate explanation
    risk_explanation = _generate_risk_explanation(
        risk_score=risk_score,
        risk_level=risk_level,
        domain=domain,
        domain_multiplier=domain_multiplier,
        detected_failures=detected_failures,
        contributing_factors=contributing_factors,
    )
    
    return {
        "risk_score": round(risk_score, 3),
        "risk_level": risk_level,
        "domain_multiplier": domain_multiplier,
        "contributing_factors": contributing_factors,
        "risk_explanation": risk_explanation,
        "node_times": {**state.get("node_times", {}), "risk_scoring": time.time() - start_time},
    }


def _generate_risk_explanation(
    risk_score: float,
    risk_level: str,
    domain: str,
    domain_multiplier: float,
    detected_failures: list,
    contributing_factors: list,
) -> str:
    """
    Generate a human-readable risk explanation.
    
    Args:
        risk_score: Calculated risk score
        risk_level: Risk level category
        domain: Analysis domain
        domain_multiplier: Applied domain multiplier
        detected_failures: List of detected failures
        contributing_factors: Breakdown of risk contributors
    
    Returns:
        Human-readable explanation string
    """
    if not detected_failures:
        return (
            f"Risk Score: {risk_score:.2f} ({risk_level.upper()}). "
            "No significant failures were detected in the analysis. "
            "The LLM output appears to be reliable for the given context."
        )
    
    # Build explanation
    lines = [
        f"Risk Score: {risk_score:.2f} ({risk_level.upper()})",
        f"Domain: {domain} (multiplier: {domain_multiplier}x)",
        "",
        "Contributing Factors:",
    ]
    
    # Sort by contribution
    sorted_factors = sorted(
        contributing_factors,
        key=lambda x: x["contribution"],
        reverse=True,
    )
    
    for factor in sorted_factors[:5]:  # Top 5 contributors
        lines.append(
            f"  • {factor['failure_type'].replace('_', ' ').title()}: "
            f"{factor['confidence']:.0%} confidence, {factor['severity']} severity "
            f"(+{factor['contribution']:.3f})"
        )
    
    # Add recommendations based on risk level
    lines.append("")
    if risk_level == "critical":
        lines.append(
            "⚠️ CRITICAL: This output has significant reliability issues. "
            "Do not deploy without substantial review and correction."
        )
    elif risk_level == "high":
        lines.append(
            "⚠️ HIGH RISK: Multiple significant issues detected. "
            "Careful review and mitigation recommended before deployment."
        )
    elif risk_level == "medium":
        lines.append(
            "⚡ MODERATE RISK: Some issues detected. "
            "Review the flagged concerns before production use."
        )
    else:
        lines.append(
            "✓ LOW RISK: Minor issues detected. "
            "Standard review recommended."
        )
    
    return "\n".join(lines)

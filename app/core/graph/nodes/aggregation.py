"""
FARIS Aggregation Node

Combines signals from all failure detectors into a consolidated result.
"""

import time
from typing import Any

from app.config import get_settings
from app.core.graph.state import AnalysisState, FailureSignal

settings = get_settings()


async def aggregation_node(state: AnalysisState) -> dict[str, Any]:
    """
    Aggregate all failure detection signals.
    
    This node:
    1. Collects signals from all detectors
    2. Filters by confidence threshold
    3. Removes duplicates
    4. Normalizes confidence scores
    
    Args:
        state: Current analysis state
    
    Returns:
        Updated state with detected_failures, failure_detected, failure_types
    """
    start_time = time.time()
    
    threshold = settings.failure_confidence_threshold
    
    # Collect all signals
    signals = []
    
    signal_keys = [
        "hallucination_signal",
        "logical_signal",
        "assumptions_signal",
        "overconfidence_signal",
        "scope_signal",
        "underspec_signal",
    ]
    
    for key in signal_keys:
        signal = state.get(key)
        if signal:
            signals.append(signal)
    
    # Filter by detection and confidence threshold
    detected_failures = []
    failure_types = []
    
    for signal in signals:
        if signal.get("detected", False):
            confidence = signal.get("confidence", 0.0)
            
            # Apply threshold
            if confidence >= threshold:
                detected_failures.append(signal)
                failure_type = signal.get("failure_type", "unknown")
                if failure_type not in failure_types:
                    failure_types.append(failure_type)
    
    # Sort by confidence (highest first)
    detected_failures.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    
    # Determine if any failure was detected
    failure_detected = len(detected_failures) > 0
    
    # Also include all signals in failure_signals for reference
    failure_signals = signals
    
    return {
        "failure_signals": failure_signals,
        "detected_failures": detected_failures,
        "failure_detected": failure_detected,
        "failure_types": failure_types,
        "node_times": {**state.get("node_times", {}), "aggregation": time.time() - start_time},
    }

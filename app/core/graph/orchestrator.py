"""
FARIS LangGraph Orchestrator

Main workflow orchestration that connects all nodes into a cohesive
analysis pipeline with parallel execution where possible.
"""

import asyncio
import time
from typing import Any, Optional

from langgraph.graph import StateGraph, END

from app.core.graph.state import AnalysisState, create_initial_state
from app.core.graph.nodes.precheck import precheck_node
from app.core.graph.nodes.decomposition import decomposition_node
from app.core.graph.nodes.aggregation import aggregation_node
from app.core.graph.nodes.explanation import explanation_node
from app.core.graph.nodes.risk_scoring import risk_scoring_node
from app.core.graph.nodes.recommendation import recommendation_node
from app.core.graph.nodes.detectors import (
    hallucination_detector,
    logical_inconsistency_detector,
    missing_assumptions_detector,
    overconfidence_detector,
    scope_violation_detector,
    underspecification_detector,
)


def should_continue_after_precheck(state: AnalysisState) -> str:
    """
    Determine if analysis should continue after precheck.
    
    Args:
        state: Current state
    
    Returns:
        Next node name or END
    """
    if state.get("precheck_passed", False):
        return "decomposition"
    else:
        return "early_exit"


def early_exit_node(state: AnalysisState) -> dict[str, Any]:
    """
    Handle early exit when precheck fails.
    
    Args:
        state: Current state
    
    Returns:
        Final state updates
    """
    return {
        "failure_detected": False,
        "failure_types": [],
        "detected_failures": [],
        "risk_score": 0.0,
        "risk_level": "low",
        "explanation": f"Analysis skipped: {state.get('precheck_failure_reason', 'Invalid input')}",
        "recommendations": [],
        "end_time": time.time(),
    }


async def parallel_detectors_node(state: AnalysisState) -> dict[str, Any]:
    """
    Run all failure detectors in parallel.
    
    This node executes all 6 detectors concurrently for efficiency.
    
    Args:
        state: Current state
    
    Returns:
        Combined updates from all detectors
    """
    start_time = time.time()
    
    # Run all detectors in parallel
    results = await asyncio.gather(
        hallucination_detector(state),
        logical_inconsistency_detector(state),
        missing_assumptions_detector(state),
        overconfidence_detector(state),
        scope_violation_detector(state),
        underspecification_detector(state),
        return_exceptions=True,
    )
    
    # Merge results
    merged = {}
    errors = state.get("errors", [])
    
    for result in results:
        if isinstance(result, Exception):
            errors.append({"node": "parallel_detectors", "error": str(result)})
        elif isinstance(result, dict):
            # Merge node_times specially
            if "node_times" in result:
                existing_times = merged.get("node_times", {})
                existing_times.update(result.pop("node_times"))
                merged["node_times"] = existing_times
            merged.update(result)
    
    merged["errors"] = errors
    merged["node_times"] = {
        **merged.get("node_times", {}),
        "parallel_detectors_total": time.time() - start_time,
    }
    
    return merged


def finalize_node(state: AnalysisState) -> dict[str, Any]:
    """
    Finalize the analysis state.
    
    Args:
        state: Current state
    
    Returns:
        Final updates
    """
    return {
        "end_time": time.time(),
    }


def create_analysis_graph() -> StateGraph:
    """
    Create the FARIS analysis workflow graph.
    
    The graph structure:
    
    START
      │
      ▼
    Precheck ──────────────► Early Exit (if failed)
      │                           │
      ▼                           ▼
    Decomposition                END
      │
      ▼
    Parallel Detectors (6 detectors run concurrently)
      │
      ▼
    Aggregation
      │
      ▼
    Risk Scoring
      │
      ▼
    Explanation
      │
      ▼
    Recommendation
      │
      ▼
    Finalize
      │
      ▼
    END
    
    Returns:
        Compiled StateGraph
    """
    # Create the graph
    workflow = StateGraph(AnalysisState)
    
    # Add nodes
    workflow.add_node("precheck", precheck_node)
    workflow.add_node("early_exit", early_exit_node)
    workflow.add_node("decomposition", decomposition_node)
    workflow.add_node("parallel_detectors", parallel_detectors_node)
    workflow.add_node("aggregation", aggregation_node)
    workflow.add_node("risk_scoring", risk_scoring_node)
    workflow.add_node("explanation", explanation_node)
    workflow.add_node("recommendation", recommendation_node)
    workflow.add_node("finalize", finalize_node)
    
    # Set entry point
    workflow.set_entry_point("precheck")
    
    # Add conditional edge after precheck
    workflow.add_conditional_edges(
        "precheck",
        should_continue_after_precheck,
        {
            "decomposition": "decomposition",
            "early_exit": "early_exit",
        },
    )
    
    # Linear flow after decomposition
    workflow.add_edge("decomposition", "parallel_detectors")
    workflow.add_edge("parallel_detectors", "aggregation")
    workflow.add_edge("aggregation", "risk_scoring")
    workflow.add_edge("risk_scoring", "explanation")
    workflow.add_edge("explanation", "recommendation")
    workflow.add_edge("recommendation", "finalize")
    
    # End points
    workflow.add_edge("early_exit", END)
    workflow.add_edge("finalize", END)
    
    return workflow.compile()


# Cached compiled graph
_compiled_graph = None


def get_analysis_graph():
    """Get the compiled analysis graph (cached)."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = create_analysis_graph()
    return _compiled_graph


async def run_analysis(
    question: str,
    answer: str,
    context: Optional[str] = None,
    domain: str = "general",
    model_metadata: Optional[dict] = None,
) -> AnalysisState:
    """
    Run the complete FARIS analysis pipeline.
    
    This is the main entry point for analysis. It:
    1. Creates the initial state
    2. Runs the LangGraph workflow
    3. Returns the final state
    
    Args:
        question: The original question
        answer: The LLM's answer to analyze
        context: Additional context if provided
        domain: Analysis domain (general, medical, legal, finance, code)
        model_metadata: Information about the model that generated the answer
    
    Returns:
        Final AnalysisState with all results
    
    Example:
        result = await run_analysis(
            question="What is the capital of France?",
            answer="Paris is the capital, founded in 100 AD.",
            domain="general"
        )
        print(result["risk_score"])  # e.g., 0.65
    """
    # Create initial state
    initial_state = create_initial_state(
        question=question,
        answer=answer,
        context=context,
        domain=domain,
        model_metadata=model_metadata,
    )
    
    # Get compiled graph
    graph = get_analysis_graph()
    
    # Run the graph
    final_state = await graph.ainvoke(initial_state)
    
    return final_state

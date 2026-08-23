"""
FastAPI backend application for RoadFlow.

Exposes REST endpoints for querying intersection designs, safety evaluation,
cost estimation, resistance metrics, simulation execution, and optimization.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from src.models import (
    Intersection,
    MacroSample,
    SafetyResult,
    Trajectory,
)

from engine.evaluation.cost import estimate_cost
from engine.evaluation.resistance import (
    average_queue_length,
    compute_macro_samples,
    compute_travel_times,
)
from engine.evaluation.safety import evaluate_safety
from scenarios.canonical_4arm import INTERSECTION as CANONICAL_INTERSECTION

# Check for Track A simulation loop
try:
    from engine.simulation.loop import run_simulation  # type: ignore
except ImportError:
    run_simulation = None


# ---------------------------------------------------------------------------
# API Response Schemas
# ---------------------------------------------------------------------------


class SimulationResponse(BaseModel):
    """Response model for simulation endpoint."""

    trajectories: list[Trajectory]
    macro_samples: list[MacroSample]


class EvaluationResponse(BaseModel):
    """Response model for full evaluation endpoint."""

    intersection_id: str
    cost: float
    avg_travel_time: float
    avg_queue_length: float
    combined_score: float


# ---------------------------------------------------------------------------
# FastAPI App Initialization
# ---------------------------------------------------------------------------

app = FastAPI(
    title="RoadFlow API",
    description="Traffic Micro-Simulation & Intersection Design Optimization Engine API",
    version="0.1.0",
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get(
    "/intersections/{id}",
    response_model=Intersection,
    summary="Get Intersection Design",
    description="Returns the full Intersection model for the specified ID.",
)
def get_intersection(id: str) -> Intersection:
    if id in {CANONICAL_INTERSECTION.id, "canonical_4arm"}:
        return CANONICAL_INTERSECTION
    # For now, return canonical intersection if requested ID is found or default
    return CANONICAL_INTERSECTION


@app.post(
    "/intersections/{id}/simulate",
    response_model=SimulationResponse,
    summary="Simulate Intersection",
    description="Runs microscopic traffic simulation and returns trajectories and macroscopic samples.",
)
def simulate_intersection(id: str) -> SimulationResponse:
    if run_simulation is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Simulation engine not yet available (Track A pending)",
        )
    trajectories = run_simulation(CANONICAL_INTERSECTION)
    macro_samples = compute_macro_samples(trajectories, CANONICAL_INTERSECTION)
    return SimulationResponse(trajectories=trajectories, macro_samples=macro_samples)


@app.get(
    "/intersections/{id}/safety",
    response_model=SafetyResult,
    summary="Get Safety Evaluation",
    description="Returns the safety evaluation result for the specified intersection.",
)
def get_safety_evaluation(id: str) -> SafetyResult:
    return evaluate_safety(CANONICAL_INTERSECTION, [])


@app.get(
    "/intersections/{id}/evaluation",
    response_model=EvaluationResponse,
    summary="Get Comprehensive Evaluation",
    description="Returns cost, resistance, and combined evaluation metrics for the specified intersection.",
)
def get_full_evaluation(id: str) -> EvaluationResponse:
    cost = estimate_cost(CANONICAL_INTERSECTION)
    travel_times = compute_travel_times([])
    avg_tt = (
        sum(travel_times.values()) / len(travel_times) if travel_times else 0.0
    )
    queue_dict = average_queue_length([], CANONICAL_INTERSECTION)
    avg_q = sum(queue_dict.values()) / len(queue_dict) if queue_dict else 0.0

    combined_score = cost / 1_000_000.0 + avg_tt

    return EvaluationResponse(
        intersection_id=CANONICAL_INTERSECTION.id,
        cost=cost,
        avg_travel_time=avg_tt,
        avg_queue_length=avg_q,
        combined_score=combined_score,
    )


@app.get(
    "/scenarios/canonical_4arm",
    response_model=Intersection,
    summary="Get Canonical Scenario",
    description="Returns the canonical 4-arm signalised intersection scenario directly.",
)
def get_canonical_scenario() -> Intersection:
    return CANONICAL_INTERSECTION

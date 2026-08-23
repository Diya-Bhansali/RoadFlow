"""
Grid search optimizer for RoadFlow intersection designs.

Evaluates a parameter grid of lane counts, signal splits, and curve radii to
find optimal intersection configurations that pass safety checks and minimize
a combined cost and travel-time objective score.
"""

from __future__ import annotations

import math
from typing import Any

from src.models import (
    Intersection,
    Lane,
    Path,
    PathPoint,
    SafetyResult,
    Signal,
    SignalPhase,
    Trajectory,
)

from engine.evaluation.cost import estimate_cost
from engine.evaluation.resistance import (
    average_queue_length,
    compute_travel_times,
)
from engine.evaluation.safety import evaluate_safety
from scenarios.canonical_4arm import (
    DEMAND_RECORDS,
    INTERSECTION as CANONICAL_INTERSECTION,
)

# NOTE: Track A simulation engine (engine.simulation.loop.run_simulation) is pending integration.
# When engine.simulation.loop becomes available, run_simulation(intersection) will be called
# to generate dynamic trajectories.
try:
    from engine.simulation.loop import run_simulation  # type: ignore
except ImportError:
    run_simulation = None

# Parameter Grid Definition
LANE_COUNTS: list[int] = [2, 3, 4]
SIGNAL_SPLITS: list[list[float]] = [
    [45.0, 15.0, 35.0, 25.0],
    [40.0, 20.0, 40.0, 20.0],
    [50.0, 10.0, 30.0, 30.0],
]
CURVE_RADII: list[float] = [8.0, 12.0, 16.0]


def build_modified_intersection(
    base: Intersection,
    lane_count: int,
    signal_split: list[float],
    curve_radius: float,
) -> Intersection:
    """Build a modified Intersection model using specified design parameters.

    Parameters
    ----------
    base : Intersection
        Base intersection template to copy non-modified fields from.
    lane_count : int
        Number of lanes per approach arm (N, S, E, W).
    signal_split : list[float]
        Phase durations in seconds for the 4 signal phases.
    curve_radius : float
        Radius in metres for curved path points (curvature = 1 / curve_radius).

    Returns
    -------
    Intersection
        New Intersection instance with updated lanes, paths, and signal settings.
    """
    approaches = ["N", "S", "E", "W"]
    vehicle_classes = ["Passenger Car", "Two-Wheeler", "Auto-Rickshaw"]

    # 1. Build Lanes
    new_lanes: list[Lane] = []
    for app in approaches:
        for i in range(lane_count):
            lane_id = f"{app}-L{i+1}"
            movements = ["left"] if i == 0 else (["right"] if i == lane_count - 1 else ["through"])
            new_lanes.append(
                Lane(
                    id=lane_id,
                    approach=app,
                    width_m=3.5,
                    allowed_movements=movements,
                    vehicle_classes=vehicle_classes,
                )
            )

    # 2. Build Signal
    new_phases: list[SignalPhase] = []
    for i, duration in enumerate(signal_split):
        orig_phase = base.signal.phases[i] if i < len(base.signal.phases) else None
        active_ids = orig_phase.active_movement_ids if orig_phase else []
        new_phases.append(
            SignalPhase(
                id=f"P{i+1}",
                active_movement_ids=active_ids,
                duration_s=duration,
            )
        )

    new_signal = Signal(
        id=base.signal.id,
        cycle_s=sum(signal_split),
        phases=new_phases,
    )

    # 3. Build Paths with modified curvature
    new_paths: list[Path] = []
    target_curvature = 1.0 / curve_radius if curve_radius != 0 else 0.0

    for path in base.paths:
        new_points: list[PathPoint] = []
        for pt in path.points:
            c = 0.0
            if not math.isclose(pt.curvature, 0.0):
                c = target_curvature if pt.curvature > 0 else -target_curvature
            new_points.append(
                PathPoint(s=pt.s, x=pt.x, y=pt.y, curvature=c)
            )
        new_paths.append(
            Path(
                id=path.id,
                entry_lane_id=path.entry_lane_id,
                exit_lane_id=path.exit_lane_id,
                movement=path.movement,
                points=new_points,
                speed_limit_mps=path.speed_limit_mps,
            )
        )

    return Intersection(
        id=f"{base.id}_L{lane_count}_R{int(curve_radius)}",
        name=f"{base.name} ({lane_count} lanes, R={curve_radius}m)",
        lanes=new_lanes,
        paths=new_paths,
        signal=new_signal,
    )


def run_optimization(
    base_intersection: Intersection | None = None,
) -> list[dict[str, Any]]:
    """Execute grid search optimization over all parameter combinations.

    Evaluates grid of lane_counts x signal_splits x curve_radii.
    Filters out infeasible designs and ranks remaining by combined score
    0.4 * norm_cost + 0.6 * norm_avg_travel_time.

    Parameters
    ----------
    base_intersection : Intersection | None
        Base intersection design template. Defaults to CANONICAL_INTERSECTION.

    Returns
    -------
    list[dict[str, Any]]
        Ranked list of evaluated feasible design results.
    """
    if base_intersection is None:
        base_intersection = CANONICAL_INTERSECTION

    raw_results: list[dict[str, Any]] = []

    for lane_count in LANE_COUNTS:
        for signal_split in SIGNAL_SPLITS:
            for curve_radius in CURVE_RADII:
                intersection = build_modified_intersection(
                    base_intersection, lane_count, signal_split, curve_radius
                )

                # Execute Track A simulation engine if available, else skip
                trajectories: list[Trajectory] = []
                if run_simulation is not None:
                    # Trajectories returned by simulation loop
                    trajectories = run_simulation(intersection, DEMAND_RECORDS)

                safety_res: SafetyResult = evaluate_safety(intersection, trajectories)
                cost_val: float = estimate_cost(intersection)

                travel_times = compute_travel_times(trajectories)
                avg_tt = (
                    sum(travel_times.values()) / len(travel_times)
                    if travel_times
                    else 0.0
                )

                queue_dict = average_queue_length(trajectories, intersection)
                avg_q = (
                    sum(queue_dict.values()) / len(queue_dict)
                    if queue_dict
                    else 0.0
                )

                raw_results.append(
                    {
                        "design_params": {
                            "lane_count": lane_count,
                            "signal_split": signal_split,
                            "curve_radius": curve_radius,
                        },
                        "safety_result": safety_res,
                        "cost": cost_val,
                        "avg_travel_time": avg_tt,
                        "avg_queue_length": avg_q,
                        "feasible": safety_res.feasible,
                        "intersection": intersection,
                    }
                )

    # Filter out infeasible designs
    feasible_results = [r for r in raw_results if r["feasible"]]

    if not feasible_results:
        return []

    # Compute min/max for normalization
    costs = [r["cost"] for r in feasible_results]
    tts = [r["avg_travel_time"] for r in feasible_results]

    min_cost, max_cost = min(costs), max(costs)
    min_tt, max_tt = min(tts), max(tts)

    for r in feasible_results:
        norm_cost = (
            (r["cost"] - min_cost) / (max_cost - min_cost)
            if max_cost > min_cost
            else 0.0
        )
        norm_tt = (
            (r["avg_travel_time"] - min_tt) / (max_tt - min_tt)
            if max_tt > min_tt
            else 0.0
        )
        r["score"] = 0.4 * norm_cost + 0.6 * norm_tt
        r["recommended"] = False

    # Rank by score ascending (lower is better)
    ranked_results = sorted(feasible_results, key=lambda x: x["score"])

    # Mark top result as recommended
    if ranked_results:
        ranked_results[0]["recommended"] = True

    return ranked_results


# Alias for flexible importing
optimize = run_optimization

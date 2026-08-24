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
            if lane_count == 2:
                movements = ["left"] if i == 0 else ["through", "right"]
            else:
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

    # Geometry constants matching canonical_4arm
    HALF_BOX = 10.0
    RUN_OUT = 30.0
    LANE_WIDTH = 3.5
    SPEED_THROUGH = 11.1
    SPEED_TURN = 5.0
    _NS_ENTRY = HALF_BOX + RUN_OUT
    _NS_EXIT = -(HALF_BOX + RUN_OUT)
    _EW_ENTRY = HALF_BOX + RUN_OUT
    _EW_EXIT = -(HALF_BOX + RUN_OUT)

    def _n_off(i: int) -> float:
        return -(i + 0.5) * LANE_WIDTH

    def _s_off(i: int) -> float:
        return (i + 0.5) * LANE_WIDTH

    def _e_off(i: int) -> float:
        return (i + 0.5) * LANE_WIDTH

    def _w_off(i: int) -> float:
        return -(i + 0.5) * LANE_WIDTH

    target_curvature = 1.0 / curve_radius if curve_radius != 0 else 0.0

    def _points_turn(
        x0: float, y0: float, xm: float, ym: float, x1: float, y1: float, curvature: float
    ) -> list[PathPoint]:
        leg1 = math.sqrt((xm - x0) ** 2 + (ym - y0) ** 2)
        leg2 = math.sqrt((x1 - xm) ** 2 + (y1 - ym) ** 2)
        total = leg1 + leg2
        return [
            PathPoint(s=0.0, x=x0, y=y0, curvature=0.0),
            PathPoint(s=leg1, x=xm, y=ym, curvature=curvature),
            PathPoint(s=total, x=x1, y=y1, curvature=0.0),
        ]

    def _points_straight(
        x0: float, y0: float, x1: float, y1: float, n: int = 5
    ) -> list[PathPoint]:
        length = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
        step = length / (n - 1)
        return [
            PathPoint(
                s=i * step,
                x=x0 + (x1 - x0) * i / (n - 1),
                y=y0 + (y1 - y0) * i / (n - 1),
                curvature=0.0,
            )
            for i in range(n)
        ]

    through_indices = [1] if lane_count == 2 else list(range(1, lane_count - 1))
    through_lane_nums = [idx + 1 for idx in through_indices]
    r_idx = lane_count - 1
    r_num = lane_count

    new_paths: list[Path] = []

    # 2. Build Through Paths
    for k, i in zip(through_lane_nums, through_indices):
        new_paths.append(
            Path(
                id=f"N-L{k}_to_S-L{k}",
                entry_lane_id=f"N-L{k}",
                exit_lane_id=f"S-L{k}",
                movement="through",
                points=_points_straight(_n_off(i), _NS_ENTRY, _n_off(i), _NS_EXIT),
                speed_limit_mps=SPEED_THROUGH,
            )
        )
        new_paths.append(
            Path(
                id=f"S-L{k}_to_N-L{k}",
                entry_lane_id=f"S-L{k}",
                exit_lane_id=f"N-L{k}",
                movement="through",
                points=_points_straight(_s_off(i), -_NS_ENTRY, _s_off(i), -_NS_EXIT),
                speed_limit_mps=SPEED_THROUGH,
            )
        )
        new_paths.append(
            Path(
                id=f"E-L{k}_to_W-L{k}",
                entry_lane_id=f"E-L{k}",
                exit_lane_id=f"W-L{k}",
                movement="through",
                points=_points_straight(_EW_ENTRY, _e_off(i), _EW_EXIT, _e_off(i)),
                speed_limit_mps=SPEED_THROUGH,
            )
        )
        new_paths.append(
            Path(
                id=f"W-L{k}_to_E-L{k}",
                entry_lane_id=f"W-L{k}",
                exit_lane_id=f"E-L{k}",
                movement="through",
                points=_points_straight(-_EW_ENTRY, _w_off(i), -_EW_EXIT, _w_off(i)),
                speed_limit_mps=SPEED_THROUGH,
            )
        )

    # 3. Build Left-turn Paths
    new_paths.append(
        Path(
            id="N-L1_to_E-L1",
            entry_lane_id="N-L1",
            exit_lane_id="E-L1",
            movement="left",
            points=_points_turn(
                _n_off(0), _NS_ENTRY, -HALF_BOX / 2, HALF_BOX / 2, _EW_EXIT, _e_off(0), target_curvature
            ),
            speed_limit_mps=SPEED_TURN,
        )
    )
    new_paths.append(
        Path(
            id="S-L1_to_W-L1",
            entry_lane_id="S-L1",
            exit_lane_id="W-L1",
            movement="left",
            points=_points_turn(
                _s_off(0), -_NS_ENTRY, HALF_BOX / 2, -HALF_BOX / 2, -_EW_EXIT, _w_off(0), target_curvature
            ),
            speed_limit_mps=SPEED_TURN,
        )
    )
    new_paths.append(
        Path(
            id="E-L1_to_S-L1",
            entry_lane_id="E-L1",
            exit_lane_id="S-L1",
            movement="left",
            points=_points_turn(
                _EW_ENTRY, _e_off(0), HALF_BOX / 2, HALF_BOX / 2, _s_off(0), _NS_EXIT, target_curvature
            ),
            speed_limit_mps=SPEED_TURN,
        )
    )
    new_paths.append(
        Path(
            id="W-L1_to_N-L1",
            entry_lane_id="W-L1",
            exit_lane_id="N-L1",
            movement="left",
            points=_points_turn(
                -_EW_ENTRY, _w_off(0), -HALF_BOX / 2, -HALF_BOX / 2, _n_off(0), -_NS_EXIT, target_curvature
            ),
            speed_limit_mps=SPEED_TURN,
        )
    )

    # 4. Build Right-turn Paths
    new_paths.append(
        Path(
            id=f"N-L{r_num}_to_W-L{r_num}",
            entry_lane_id=f"N-L{r_num}",
            exit_lane_id=f"W-L{r_num}",
            movement="right",
            points=_points_turn(
                _n_off(r_idx), _NS_ENTRY, -HALF_BOX / 2, HALF_BOX / 2, -_EW_EXIT, _w_off(r_idx), target_curvature
            ),
            speed_limit_mps=SPEED_TURN,
        )
    )
    new_paths.append(
        Path(
            id=f"S-L{r_num}_to_E-L{r_num}",
            entry_lane_id=f"S-L{r_num}",
            exit_lane_id=f"E-L{r_num}",
            movement="right",
            points=_points_turn(
                _s_off(r_idx), -_NS_ENTRY, HALF_BOX / 2, -HALF_BOX / 2, _EW_EXIT, _e_off(r_idx), target_curvature
            ),
            speed_limit_mps=SPEED_TURN,
        )
    )
    new_paths.append(
        Path(
            id=f"E-L{r_num}_to_N-L{r_num}",
            entry_lane_id=f"E-L{r_num}",
            exit_lane_id=f"N-L{r_num}",
            movement="right",
            points=_points_turn(
                _EW_ENTRY, _e_off(r_idx), HALF_BOX / 2, HALF_BOX / 2, _n_off(r_idx), -_NS_EXIT, target_curvature
            ),
            speed_limit_mps=SPEED_TURN,
        )
    )
    new_paths.append(
        Path(
            id=f"W-L{r_num}_to_S-L{r_num}",
            entry_lane_id=f"W-L{r_num}",
            exit_lane_id=f"S-L{r_num}",
            movement="right",
            points=_points_turn(
                -_EW_ENTRY, _w_off(r_idx), -HALF_BOX / 2, -HALF_BOX / 2, _s_off(r_idx), _NS_EXIT, target_curvature
            ),
            speed_limit_mps=SPEED_TURN,
        )
    )

    # 5. Build Signal Phases
    p1_active = (
        [f"N-L{k}_to_S-L{k}" for k in through_lane_nums]
        + [f"S-L{k}_to_N-L{k}" for k in through_lane_nums]
        + [f"N-L{r_num}_to_W-L{r_num}", f"S-L{r_num}_to_E-L{r_num}"]
    )
    p2_active = (
        [f"E-L{k}_to_W-L{k}" for k in through_lane_nums]
        + [f"W-L{k}_to_E-L{k}" for k in through_lane_nums]
        + [f"E-L{r_num}_to_N-L{r_num}", f"W-L{r_num}_to_S-L{r_num}"]
    )
    p3_active = ["N-L1_to_E-L1", "S-L1_to_W-L1"]
    p4_active = ["E-L1_to_S-L1", "W-L1_to_N-L1"]

    phase_actives = [p1_active, p2_active, p3_active, p4_active]
    new_phases: list[SignalPhase] = []
    for i, duration in enumerate(signal_split):
        new_phases.append(
            SignalPhase(
                id=f"P{i+1}",
                active_movement_ids=phase_actives[i] if i < len(phase_actives) else [],
                duration_s=duration,
            )
        )

    new_signal = Signal(
        id=base.signal.id,
        cycle_s=sum(signal_split),
        phases=new_phases,
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
                    trajectories = run_simulation(
                        intersection, DEMAND_RECORDS, duration_s=10.0
                    )

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

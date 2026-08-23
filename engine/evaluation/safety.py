"""
Safety evaluation engine for RoadFlow intersection configurations.

Provides ``evaluate_safety`` — a single-pass feasibility check that inspects a
list of vehicle trajectories against an intersection definition and returns a
``SafetyResult`` summarising violations (if any) and the tightest safety margin.

Three independent checks are performed:

1. **Minimum-gap violation** — vehicles on the same path must maintain at least
   ``max(0.5 s × speed, 2 m)`` of following distance at every time step.
2. **Conflict-point safety** — paths whose geometry crosses within 1.5 m must
   not have vehicles from different trajectories occupying the crossing zone
   within 1.5 s of each other.
3. **Signal violation** — every trajectory must proceed only during a signal
   phase whose ``active_movement_ids`` include the trajectory's ``path_id``.
"""

from __future__ import annotations

import math
from itertools import combinations

from src.models import (
    Intersection,
    Path,
    PathPoint,
    SafetyResult,
    Trajectory,
    TrajectoryPoint,
)

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

MIN_FOLLOWING_TIME_S: float = 0.5
"""Minimum time-headway in seconds for vehicles on the same path."""

MIN_FOLLOWING_DIST_M: float = 2.0
"""Absolute minimum gap in metres regardless of speed."""

CONFLICT_POINT_DIST_M: float = 1.5
"""Maximum geometric distance (metres) between path points to be considered
a shared crossing zone."""

CONFLICT_TIME_WINDOW_S: float = 1.5
"""Minimum temporal separation (seconds) for vehicles passing through a shared
crossing zone."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _required_gap(speed_mps: float) -> float:
    """Return the safe gap in metres for a given speed.

    The gap is the larger of *MIN_FOLLOWING_TIME_S × speed* and
    *MIN_FOLLOWING_DIST_M*, ensuring a floor even at very low speeds.
    """
    return max(MIN_FOLLOWING_TIME_S * speed_mps, MIN_FOLLOWING_DIST_M)


def _interpolate_time_at_s(
    points: list[TrajectoryPoint],
    target_s: float,
) -> float | None:
    """Linearly interpolate the time at which a vehicle reaches *target_s*.

    Returns ``None`` if *target_s* falls outside the trajectory's coverage.
    """
    for i in range(len(points) - 1):
        s0, s1 = points[i].s, points[i + 1].s
        if s0 <= target_s <= s1:
            if math.isclose(s1, s0):
                return points[i].t
            frac = (target_s - s0) / (s1 - s0)
            return points[i].t + frac * (points[i + 1].t - points[i].t)
    # target_s may exactly equal the last point
    if points and math.isclose(points[-1].s, target_s):
        return points[-1].t
    return None


def _find_crossing_s_pairs(
    path_a: Path,
    path_b: Path,
) -> list[tuple[float, float]]:
    """Return *(s_a, s_b)* pairs where path geometries come within the
    conflict-point distance threshold.

    Each pair represents a crossing zone where vehicles on the two paths could
    potentially collide.
    """
    pairs: list[tuple[float, float]] = []
    for pt_a in path_a.points:
        for pt_b in path_b.points:
            dx = pt_a.x - pt_b.x
            dy = pt_a.y - pt_b.y
            dist = math.hypot(dx, dy)
            if dist <= CONFLICT_POINT_DIST_M:
                pairs.append((pt_a.s, pt_b.s))
    return pairs


def _active_path_ids_at(intersection: Intersection, time_s: float) -> set[str]:
    """Return the set of path IDs that have an active (green) signal at *time_s*.

    Signal phases are applied cyclically using *signal.cycle_s*.
    """
    signal = intersection.signal
    cycle_time = time_s % signal.cycle_s
    elapsed = 0.0
    for phase in signal.phases:
        if elapsed <= cycle_time < elapsed + phase.duration_s:
            return set(phase.active_movement_ids)
        elapsed += phase.duration_s
    # Fallback: last phase covers any rounding edge
    return set(signal.phases[-1].active_movement_ids) if signal.phases else set()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def evaluate_safety(
    intersection: Intersection,
    trajectories: list[Trajectory],
) -> SafetyResult:
    """Run all safety checks and return a ``SafetyResult``.

    Parameters
    ----------
    intersection:
        The intersection definition (lanes, paths, signal).
    trajectories:
        All vehicle trajectories to evaluate.

    Returns
    -------
    SafetyResult
        Contains ``feasible``, ``margin``, and human-readable ``violations``.
    """
    violations: list[str] = []
    # Start with a large positive margin; each check may tighten it.
    tightest_margin: float = float("inf")

    # Build lookup: path_id → Path model
    path_by_id: dict[str, Path] = {p.id: p for p in intersection.paths}

    # ------------------------------------------------------------------
    # 1. Minimum-gap violation (same-path following distance)
    # ------------------------------------------------------------------
    # Group trajectories by path_id
    trajs_by_path: dict[str, list[Trajectory]] = {}
    for traj in trajectories:
        trajs_by_path.setdefault(traj.path_id, []).append(traj)

    for path_id, group in trajs_by_path.items():
        if len(group) < 2:
            continue
        # Compare every pair on the same path at every shared time step.
        for i, traj_a in enumerate(group):
            for traj_b in group[i + 1 :]:
                # Build time → s maps for both trajectories
                time_to_s_a = {pt.t: (pt.s, pt.speed_mps) for pt in traj_a.points}
                time_to_s_b = {pt.t: (pt.s, pt.speed_mps) for pt in traj_b.points}
                common_times = sorted(set(time_to_s_a) & set(time_to_s_b))
                for t in common_times:
                    s_a, spd_a = time_to_s_a[t]
                    s_b, spd_b = time_to_s_b[t]
                    gap = abs(s_a - s_b)
                    # Use the speed of the trailing vehicle (or max of both)
                    ref_speed = max(spd_a, spd_b)
                    required = _required_gap(ref_speed)
                    margin = gap - required
                    if margin < tightest_margin:
                        tightest_margin = margin
                    if margin < 0:
                        violations.append(
                            f"Gap violation on path {path_id}: vehicles "
                            f"{traj_a.vehicle_id} and {traj_b.vehicle_id} "
                            f"are {gap:.2f} m apart at t={t:.2f} s "
                            f"(required {required:.2f} m)"
                        )

    # ------------------------------------------------------------------
    # 2. Conflict-point safety (crossing paths)
    # ------------------------------------------------------------------
    checked_path_pairs: set[tuple[str, str]] = set()
    for (traj_a, traj_b) in combinations(trajectories, 2):
        if traj_a.path_id == traj_b.path_id:
            continue  # same-path is handled by check 1
        pair_key = tuple(sorted((traj_a.path_id, traj_b.path_id)))
        path_a = path_by_id.get(traj_a.path_id)
        path_b = path_by_id.get(traj_b.path_id)
        if path_a is None or path_b is None:
            continue

        # Compute crossing s pairs once per path pair
        if pair_key not in checked_path_pairs:
            crossing_pairs = _find_crossing_s_pairs(path_a, path_b)
            checked_path_pairs.add(pair_key)
        else:
            crossing_pairs = _find_crossing_s_pairs(path_a, path_b)

        for s_a, s_b in crossing_pairs:
            t_a = _interpolate_time_at_s(traj_a.points, s_a)
            t_b = _interpolate_time_at_s(traj_b.points, s_b)
            if t_a is None or t_b is None:
                continue
            time_gap = abs(t_a - t_b)
            margin = time_gap - CONFLICT_TIME_WINDOW_S
            if margin < tightest_margin:
                tightest_margin = margin
            if margin < 0:
                violations.append(
                    f"Conflict point on paths {traj_a.path_id} and "
                    f"{traj_b.path_id}: vehicles {traj_a.vehicle_id} and "
                    f"{traj_b.vehicle_id} pass crossing zone "
                    f"{time_gap:.2f} s apart (need {CONFLICT_TIME_WINDOW_S} s)"
                )

    # ------------------------------------------------------------------
    # 3. Signal violation
    # ------------------------------------------------------------------
    for traj in trajectories:
        for pt in traj.points:
            active_ids = _active_path_ids_at(intersection, pt.t)
            if traj.path_id not in active_ids:
                violations.append(
                    f"Signal violation: vehicle {traj.vehicle_id} on path "
                    f"{traj.path_id} proceeds at t={pt.t:.2f} s when path "
                    f"is not in active phase"
                )
                # Signal check doesn't contribute a continuous margin; use
                # a sentinel negative value to ensure feasible = False.
                if tightest_margin > -1.0:
                    tightest_margin = -1.0
                # One violation per trajectory is enough for reporting.
                break

    # ------------------------------------------------------------------
    # Finalize result
    # ------------------------------------------------------------------
    feasible = len(violations) == 0
    # If no checks ran (e.g. empty trajectories), margin should be 0.
    if math.isinf(tightest_margin):
        tightest_margin = 0.0

    return SafetyResult(
        intersection_id=intersection.id,
        feasible=feasible,
        margin=tightest_margin,
        violations=violations,
    )

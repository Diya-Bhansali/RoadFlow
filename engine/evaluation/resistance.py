"""
Resistance and travel-time evaluation engine for RoadFlow.

Provides functions for evaluating vehicle travel times, macroscopic traffic
samples (density, speed, flow), and average queue lengths per approach.
"""

from __future__ import annotations

from src.models import Intersection, MacroSample, Trajectory

QUEUE_VEHICLE_LENGTH_M: float = 4.5
"""Average effective length of a queued vehicle in metres."""

QUEUE_DISTANCE_THRESHOLD_M: float = 50.0
"""Distance along path (metres) within which a vehicle is considered near the intersection."""

DEFAULT_SPEED_THRESHOLD_MPS: float = 2.0
"""Default speed threshold (m/s) below which a vehicle is considered queued."""


def _get_approach_map(intersection: Intersection) -> dict[str, str]:
    """Map path_id to approach cardinal direction (N, S, E, W)."""
    lane_by_id = {lane.id: lane for lane in intersection.lanes}
    path_to_approach: dict[str, str] = {}
    for path in intersection.paths:
        lane = lane_by_id.get(path.entry_lane_id)
        if lane:
            path_to_approach[path.id] = lane.approach
        else:
            prefix = path.id.split("-")[0]
            if prefix in {"N", "S", "E", "W"}:
                path_to_approach[path.id] = prefix
            else:
                path_to_approach[path.id] = "UNKNOWN"
    return path_to_approach


def compute_travel_times(trajectories: list[Trajectory]) -> dict[str, float]:
    """Compute travel time in seconds for each vehicle trajectory.

    Parameters
    ----------
    trajectories : list[Trajectory]
        List of vehicle trajectories.

    Returns
    -------
    dict[str, float]
        Mapping of vehicle_id to travel time in seconds.
    """
    travel_times: dict[str, float] = {}
    for traj in trajectories:
        if not traj.points:
            travel_times[traj.vehicle_id] = 0.0
        else:
            travel_times[traj.vehicle_id] = traj.points[-1].t - traj.points[0].t
    return travel_times


def compute_macro_samples(
    trajectories: list[Trajectory],
    intersection: Intersection,
    interval_s: float = 30.0,
) -> list[MacroSample]:
    """Compute macroscopic traffic samples (density, speed, flow) per approach.

    Parameters
    ----------
    trajectories : list[Trajectory]
        List of vehicle trajectories.
    intersection : Intersection
        Intersection model defining lanes and paths.
    interval_s : float, default=30.0
        Time interval bucket size in seconds.

    Returns
    -------
    list[MacroSample]
        List of MacroSample objects aggregated by time interval and approach.
    """
    path_to_approach = _get_approach_map(intersection)

    # Group points by (bucket_index, approach)
    buckets: dict[tuple[int, str], tuple[list[float], set[str]]] = {}

    for traj in trajectories:
        approach = path_to_approach.get(traj.path_id)
        if not approach:
            prefix = traj.path_id.split("-")[0]
            approach = prefix if prefix in {"N", "S", "E", "W"} else "UNKNOWN"

        for pt in traj.points:
            bucket_idx = int(pt.t // interval_s)
            key = (bucket_idx, approach)
            if key not in buckets:
                buckets[key] = ([], set())
            speeds, veh_ids = buckets[key]
            speeds.append(pt.speed_mps)
            veh_ids.add(traj.vehicle_id)

    samples: list[MacroSample] = []
    for (bucket_idx, approach), (speeds, veh_ids) in sorted(buckets.items()):
        timestamp_s = bucket_idx * interval_s
        n_veh = len(veh_ids)
        density_veh_per_km = n_veh / 0.1
        speed_kmh = (sum(speeds) / len(speeds) * 3.6) if speeds else 0.0
        flow_veh_per_hr = n_veh * (3600.0 / interval_s)

        samples.append(
            MacroSample(
                timestamp_s=timestamp_s,
                approach=approach,
                density_veh_per_km=density_veh_per_km,
                speed_kmh=speed_kmh,
                flow_veh_per_hr=flow_veh_per_hr,
            )
        )

    return samples


def average_queue_length(
    trajectories: list[Trajectory],
    intersection: Intersection,
    speed_threshold_mps: float = DEFAULT_SPEED_THRESHOLD_MPS,
) -> dict[str, float]:
    """Compute average queue length in metres per approach across all timesteps.

    Parameters
    ----------
    trajectories : list[Trajectory]
        List of vehicle trajectories.
    intersection : Intersection
        Intersection model defining approaches via lanes.
    speed_threshold_mps : float, default=2.0
        Speed threshold in m/s below which a vehicle is considered queued.

    Returns
    -------
    dict[str, float]
        Mapping of approach to average queue length in metres.
    """
    path_to_approach = _get_approach_map(intersection)
    all_approaches = {lane.approach for lane in intersection.lanes}

    # Group trajectory points by approach and timestep t
    timestep_queued_counts: dict[str, dict[float, int]] = {
        app: {} for app in all_approaches
    }

    for traj in trajectories:
        approach = path_to_approach.get(traj.path_id)
        if not approach:
            prefix = traj.path_id.split("-")[0]
            approach = prefix if prefix in {"N", "S", "E", "W"} else "UNKNOWN"

        if approach not in timestep_queued_counts:
            timestep_queued_counts[approach] = {}

        for pt in traj.points:
            t = pt.t
            if t not in timestep_queued_counts[approach]:
                timestep_queued_counts[approach][t] = 0

            # Check if vehicle is queued: speed < threshold and within 50m of intersection (s <= 50.0)
            if pt.speed_mps < speed_threshold_mps and pt.s <= QUEUE_DISTANCE_THRESHOLD_M:
                timestep_queued_counts[approach][t] += 1

    result: dict[str, float] = {}
    for app in all_approaches:
        t_counts = timestep_queued_counts.get(app, {})
        if not t_counts:
            result[app] = 0.0
        else:
            total_queue_len = sum(
                count * QUEUE_VEHICLE_LENGTH_M for count in t_counts.values()
            )
            result[app] = total_queue_len / len(t_counts)

    return result

"""
Discrete-time microscopic traffic simulation loop.

Integrates:
- Vehicle spawning from origin-approach DemandRecords
- Signal controller phase progression
- IDM longitudinal car-following with stop-line deceleration
- Path traversal and Trajectory recording
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Sequence

from engine.physics.idm import IDMParams, compute_idm_accel, get_idm_params
from src.models import (
    DemandRecord,
    Intersection,
    Path,
    Trajectory,
    TrajectoryPoint,
)


@dataclass
class SimVehicle:
    """Internal state of an active simulated vehicle."""

    id: str
    vehicle_class: str
    path_id: str
    approach: str
    movement: str
    s: float
    speed: float
    accel: float
    params: IDMParams
    spawn_time: float
    next_accel: float = 0.0
    has_exited: bool = False
    trajectory_points: list[TrajectoryPoint] = field(default_factory=list)


def _compute_path_stop_line_s(path: Path, box_half_width: float = 10.0) -> float:
    """
    Determine the exact distance s along the path where the vehicle reaches
    the stop line at the intersection box edge (|x| <= box_half_width and |y| <= box_half_width).
    """
    points = path.points
    if not points:
        return 0.0

    # If path already starts inside the box
    if abs(points[0].x) <= box_half_width and abs(points[0].y) <= box_half_width:
        return 0.0

    for i in range(len(points) - 1):
        p0, p1 = points[i], points[i + 1]
        in1 = abs(p1.x) <= box_half_width + 1e-6 and abs(p1.y) <= box_half_width + 1e-6
        if in1:
            u_candidates: list[float] = []
            if abs(p1.x - p0.x) > 1e-6:
                for bound_x in (-box_half_width, box_half_width):
                    u = (bound_x - p0.x) / (p1.x - p0.x)
                    if 0.0 <= u <= 1.0:
                        y_at_u = p0.y + u * (p1.y - p0.y)
                        if abs(y_at_u) <= box_half_width + 1e-4:
                            u_candidates.append(u)
            if abs(p1.y - p0.y) > 1e-6:
                for bound_y in (-box_half_width, box_half_width):
                    u = (bound_y - p0.y) / (p1.y - p0.y)
                    if 0.0 <= u <= 1.0:
                        x_at_u = p0.x + u * (p1.x - p0.x)
                        if abs(x_at_u) <= box_half_width + 1e-4:
                            u_candidates.append(u)

            if u_candidates:
                return p0.s + min(u_candidates) * (p1.s - p0.s)
            return p1.s

    return min(30.0, points[-1].s * 0.4)


def _get_active_phase_movement_ids(intersection: Intersection, t: float) -> set[str]:
    """Return set of path/movement IDs with green signal at simulation time t."""
    sig = intersection.signal
    if sig.cycle_s <= 0 or not sig.phases:
        return set()

    t_in_cycle = t % sig.cycle_s
    accum = 0.0
    for phase in sig.phases:
        accum += phase.duration_s
        if t_in_cycle < accum:
            return set(phase.active_movement_ids)

    # Fallback to last phase if floating-point edge
    return set(sig.phases[-1].active_movement_ids)


def run_simulation(
    intersection: Intersection,
    demand_records: Sequence[DemandRecord],
    duration_s: float = 60.0,
    dt: float = 0.1,
    seed: int | None = 42,
) -> list[Trajectory]:
    """
    Execute a discrete microscopic traffic simulation over a given intersection.

    Parameters:
    -----------
    intersection : Intersection
        The intersection configuration (lanes, paths, signal).
    demand_records : Sequence[DemandRecord]
        List of OD demand rates across approaches, movements, and vehicle classes.
    duration_s : float
        Total simulated time in seconds (default 60.0).
    dt : float
        Simulation timestep in seconds (default 0.1).
    seed : int | None
        Random seed for reproducible vehicle spawning.

    Returns:
    --------
    list[Trajectory]: Recorded trajectory for every vehicle that entered the simulation.
    """
    rng = random.Random(seed)

    # Pre-index paths and lanes for fast lookup
    lane_by_id = {lane.id: lane for lane in intersection.lanes}
    path_by_id = {path.id: path for path in intersection.paths}
    path_lengths = {path.id: path.points[-1].s for path in intersection.paths}
    path_stop_s = {path.id: _compute_path_stop_line_s(path) for path in intersection.paths}

    # Map (approach, movement, vehicle_class) -> list of viable Path objects
    paths_for_demand: dict[tuple[str, str, str], list[Path]] = {}
    for dr in demand_records:
        key = (dr.approach, dr.movement, dr.vehicle_class)
        if key not in paths_for_demand:
            viable: list[Path] = []
            for path in intersection.paths:
                if path.movement != dr.movement:
                    continue
                entry_lane = lane_by_id.get(path.entry_lane_id)
                if not entry_lane or entry_lane.approach != dr.approach:
                    continue
                if dr.vehicle_class in entry_lane.vehicle_classes:
                    viable.append(path)
            paths_for_demand[key] = viable

    all_vehicles: list[SimVehicle] = []
    active_vehicles: list[SimVehicle] = []
    vehicle_counter = 0

    num_steps = int(round(duration_s / dt))

    for step in range(num_steps):
        t = round(step * dt, 4)
        active_movement_ids = _get_active_phase_movement_ids(intersection, t)

        # -------------------------------------------------------------------
        # 1. Spawning
        # -------------------------------------------------------------------
        for dr in demand_records:
            if dr.vehicles_per_hour <= 0:
                continue

            p_spawn = (dr.vehicles_per_hour / 3600.0) * dt
            if rng.random() >= p_spawn:
                continue

            candidate_paths = paths_for_demand.get(
                (dr.approach, dr.movement, dr.vehicle_class), []
            )
            if not candidate_paths:
                continue

            chosen_path = rng.choice(candidate_paths)
            params = get_idm_params(dr.vehicle_class)

            # Check if entrance is clear of any vehicle within (min_gap + length)
            has_space = True
            for veh in active_vehicles:
                if veh.path_id == chosen_path.id and veh.s < (params.min_gap + params.length):
                    has_space = False
                    break

            if not has_space:
                continue

            vehicle_counter += 1
            v_init = min(params.desired_speed, chosen_path.speed_limit_mps)

            new_veh = SimVehicle(
                id=f"veh_{vehicle_counter:04d}_{dr.vehicle_class.replace(' ', '')}",
                vehicle_class=dr.vehicle_class,
                path_id=chosen_path.id,
                approach=dr.approach,
                movement=dr.movement,
                s=0.0,
                speed=v_init,
                accel=0.0,
                params=params,
                spawn_time=t,
                trajectory_points=[
                    TrajectoryPoint(
                        t=t,
                        s=0.0,
                        speed_mps=round(v_init, 4),
                        accel_mps2=0.0,
                    )
                ],
            )
            active_vehicles.append(new_veh)
            all_vehicles.append(new_veh)

        # -------------------------------------------------------------------
        # 2. Acceleration calculation for each active vehicle
        # -------------------------------------------------------------------
        # Group active vehicles by path, ordered from furthest (leader) to closest (follower)
        vehicles_by_path: dict[str, list[SimVehicle]] = {}
        for veh in active_vehicles:
            vehicles_by_path.setdefault(veh.path_id, []).append(veh)

        for path_id, path_vehs in vehicles_by_path.items():
            path_vehs.sort(key=lambda v: v.s, reverse=True)
            path = path_by_id[path_id]
            is_green = path_id in active_movement_ids
            s_stop = path_stop_s[path_id]

            for i, veh in enumerate(path_vehs):
                veh_v0 = min(veh.params.desired_speed, path.speed_limit_mps)

                # Find lead vehicle on this path
                gap_lead: float | None = None
                delta_v_lead = 0.0
                if i > 0:
                    leader = path_vehs[i - 1]
                    gap_lead = leader.s - veh.s - leader.params.length
                    delta_v_lead = veh.speed - leader.speed

                # Check red signal stop-line obstacle
                gap_signal: float | None = None
                delta_v_signal = 0.0
                if not is_green and veh.s < s_stop:
                    gap_signal = s_stop - veh.s
                    delta_v_signal = veh.speed  # virtual stopped vehicle v=0

                # Select closest obstacle ahead
                if gap_signal is not None and gap_lead is not None:
                    if gap_signal < gap_lead:
                        eff_s: float | None = max(0.001, gap_signal)
                        eff_delta_v = delta_v_signal
                    else:
                        eff_s = max(0.001, gap_lead)
                        eff_delta_v = delta_v_lead
                elif gap_signal is not None:
                    eff_s = max(0.001, gap_signal)
                    eff_delta_v = delta_v_signal
                elif gap_lead is not None:
                    eff_s = max(0.001, gap_lead)
                    eff_delta_v = delta_v_lead
                else:
                    eff_s = None
                    eff_delta_v = 0.0

                veh.next_accel = compute_idm_accel(
                    v=veh.speed,
                    v0=veh_v0,
                    s=eff_s,
                    delta_v=eff_delta_v,
                    a=veh.params.max_accel,
                    b=veh.params.comfort_decel,
                    s0=veh.params.min_gap,
                    T=veh.params.time_headway,
                    delta=veh.params.delta,
                )

        # -------------------------------------------------------------------
        # 3. Kinematic update (Euler integration)
        # -------------------------------------------------------------------
        t_next = round(t + dt, 4)
        surviving_vehicles: list[SimVehicle] = []

        for veh in active_vehicles:
            new_speed = max(0.0, veh.speed + veh.next_accel * dt)
            new_s = veh.s + new_speed * dt
            veh.speed = new_speed
            veh.s = new_s
            veh.accel = veh.next_accel

            veh.trajectory_points.append(
                TrajectoryPoint(
                    t=t_next,
                    s=round(new_s, 4),
                    speed_mps=round(new_speed, 4),
                    accel_mps2=round(veh.accel, 4),
                )
            )

            # Check if vehicle has exited the path
            if new_s >= path_lengths[veh.path_id]:
                veh.has_exited = True
            else:
                surviving_vehicles.append(veh)

        active_vehicles = surviving_vehicles

    # Convert all simulated vehicles to Pydantic Trajectory models
    return [
        Trajectory(
            vehicle_id=veh.id,
            vehicle_class=veh.vehicle_class,
            path_id=veh.path_id,
            points=veh.trajectory_points,
        )
        for veh in all_vehicles
        if len(veh.trajectory_points) > 0
    ]

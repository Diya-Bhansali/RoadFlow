"""
Unit and integration tests for the microscopic traffic simulation engine.
"""

import pytest

from engine.simulation.loop import run_simulation
from scenarios.canonical_4arm import DEMAND_RECORDS, INTERSECTION
from src.models import Trajectory


# =============================================================================
# Simulation Integration Tests
# =============================================================================


def test_canonical_4arm_simulation_60s():
    """
    Running run_simulation() on the canonical_4arm scenario for 60 simulated seconds
    completes without error and produces at least one Trajectory per spawned vehicle.
    """
    trajectories = run_simulation(
        intersection=INTERSECTION,
        demand_records=DEMAND_RECORDS,
        duration_s=60.0,
        dt=0.1,
        seed=42,
    )

    # Must produce trajectories
    assert isinstance(trajectories, list)
    assert len(trajectories) > 0

    # Validate structure and values of every trajectory
    spawned_classes = set()
    for traj in trajectories:
        assert isinstance(traj, Trajectory)
        assert traj.vehicle_id != ""
        assert traj.vehicle_class in ["Passenger Car", "Two-Wheeler", "Auto-Rickshaw"]
        spawned_classes.add(traj.vehicle_class)
        assert traj.path_id in [p.id for p in INTERSECTION.paths]
        assert len(traj.points) >= 2

        # Check trajectory points
        prev_t = -1.0
        for pt in traj.points:
            assert pt.t > prev_t, "Timestamps must be strictly increasing"
            assert pt.s >= 0.0, "Position s must be non-negative"
            assert pt.speed_mps >= 0.0, "Speed must be non-negative"
            assert -20.0 <= pt.accel_mps2 <= 5.0, "Acceleration must be bounded"
            prev_t = pt.t

    # In 60 seconds with 36 demand entries, multiple classes should have spawned
    assert len(spawned_classes) >= 2


def test_simulation_seed_reproducibility():
    """
    Simulations run with the same seed produce identical trajectories.
    """
    res1 = run_simulation(
        intersection=INTERSECTION,
        demand_records=DEMAND_RECORDS,
        duration_s=20.0,
        dt=0.1,
        seed=123,
    )
    res2 = run_simulation(
        intersection=INTERSECTION,
        demand_records=DEMAND_RECORDS,
        duration_s=20.0,
        dt=0.1,
        seed=123,
    )

    assert len(res1) == len(res2)
    for t1, t2 in zip(res1, res2):
        assert t1.vehicle_id == t2.vehicle_id
        assert t1.path_id == t2.path_id
        assert len(t1.points) == len(t2.points)
        assert t1.points[-1].s == pytest.approx(t2.points[-1].s, abs=1e-3)


def test_simulation_zero_demand():
    """
    Simulation with zero demand runs without error and produces 0 trajectories.
    """
    zero_demand = [
        dr.model_copy(update={"vehicles_per_hour": 0.0}) for dr in DEMAND_RECORDS
    ]
    trajectories = run_simulation(
        intersection=INTERSECTION,
        demand_records=zero_demand,
        duration_s=10.0,
        dt=0.1,
    )
    assert len(trajectories) == 0


def test_simulation_vehicles_respect_red_signals():
    """
    Vehicles spawned on a path with a red signal do not pass the stop line
    while the signal remains red.
    """
    # Run a short simulation of 15 seconds (first 30s is Phase 1: NS through/right green, EW red)
    trajectories = run_simulation(
        intersection=INTERSECTION,
        demand_records=DEMAND_RECORDS,
        duration_s=15.0,
        dt=0.1,
        seed=42,
    )

    # In the first 15 seconds, E-L2_to_W-L2 is RED (Phase 2 starts at t=30s).
    # Any vehicle on E-L2_to_W-L2 should stop before the stop line (s <= 30.0m).
    ew_through_trajectories = [
        t for t in trajectories if t.path_id == "E-L2_to_W-L2"
    ]
    if ew_through_trajectories:
        for t in ew_through_trajectories:
            max_s = max(pt.s for pt in t.points)
            # Must stop before or at the stop line (30.0m + small numerical tolerance)
            assert max_s <= 31.0

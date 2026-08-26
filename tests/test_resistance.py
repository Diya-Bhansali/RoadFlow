"""
Pytest tests for ``engine.evaluation.resistance``.

Coverage
--------
- ``test_compute_travel_times``: vehicle with points t=0 to t=10 returns 10.0 s.
- ``test_compute_macro_samples``: simple 2-vehicle dataset produces non-negative density, speed, flow.
- ``test_average_queue_length``: correctly flags slow vehicle near stop line as queued and fast vehicle as not queued.
"""

import pytest

from src.models import (
    Intersection,
    Lane,
    MacroSample,
    Path,
    PathPoint,
    Signal,
    SignalPhase,
    Trajectory,
    TrajectoryPoint,
)

from engine.evaluation.resistance import (
    average_queue_length,
    compute_macro_samples,
    compute_travel_times,
)


# =============================================================================
# Helpers
# =============================================================================


def _pathpoint(s: float, x: float, y: float, curvature: float = 0.0) -> PathPoint:
    return PathPoint(s=s, x=x, y=y, curvature=curvature)


def _trajpoint(t: float, s: float, speed_mps: float, accel_mps2: float = 0.0) -> TrajectoryPoint:
    return TrajectoryPoint(t=t, s=s, speed_mps=speed_mps, accel_mps2=accel_mps2)


def _make_intersection() -> Intersection:
    lanes = [
        Lane(
            id="N-L1",
            approach="N",
            width_m=3.5,
            allowed_movements=["through"],
            vehicle_classes=["Passenger Car"],
        ),
        Lane(
            id="S-L1",
            approach="S",
            width_m=3.5,
            allowed_movements=["through"],
            vehicle_classes=["Passenger Car"],
        ),
    ]
    paths = [
        Path(
            id="N-L1_to_S-L1",
            entry_lane_id="N-L1",
            exit_lane_id="S-L1",
            movement="through",
            points=[
                _pathpoint(s=0.0, x=0.0, y=10.0),
                _pathpoint(s=60.0, x=0.0, y=-50.0),
            ],
            speed_limit_mps=11.1,
        )
    ]
    signal = Signal(
        id="SIG-1",
        cycle_s=60.0,
        phases=[
            SignalPhase(id="P1", active_movement_ids=["N-L1_to_S-L1"], duration_s=60.0)
        ],
    )
    return Intersection(
        id="INT-1",
        name="Test Intersection",
        lanes=lanes,
        paths=paths,
        signal=signal,
    )


# =============================================================================
# Tests
# =============================================================================


class TestTravelTimes:
    """Verify compute_travel_times."""

    def test_compute_travel_times(self):
        """Verify compute_travel_times calculates correct time difference from first to last point."""
        traj = Trajectory(
            vehicle_id="V1",
            vehicle_class="Passenger Car",
            path_id="N-L1_to_S-L1",
            points=[
                _trajpoint(t=0.0, s=0.0, speed_mps=10.0),
                _trajpoint(t=5.0, s=25.0, speed_mps=10.0),
                _trajpoint(t=10.0, s=50.0, speed_mps=10.0),
            ],
        )

        travel_times = compute_travel_times([traj])

        assert "V1" in travel_times
        assert travel_times["V1"] == pytest.approx(10.0)

    def test_empty_trajectory_travel_time(self):
        """Verify empty trajectory returns zero travel time."""
        traj = Trajectory(
            vehicle_id="V_EMPTY",
            vehicle_class="Passenger Car",
            path_id="N-L1_to_S-L1",
            points=[],
        )

        travel_times = compute_travel_times([traj])

        assert travel_times["V_EMPTY"] == 0.0


class TestMacroSamples:
    """Verify compute_macro_samples."""

    def test_compute_macro_samples_sensible_values(self):
        """Verify compute_macro_samples produces non-negative density, speed, and flow values."""
        intersection = _make_intersection()

        traj1 = Trajectory(
            vehicle_id="V1",
            vehicle_class="Passenger Car",
            path_id="N-L1_to_S-L1",
            points=[
                _trajpoint(t=0.0, s=0.0, speed_mps=10.0),
                _trajpoint(t=10.0, s=30.0, speed_mps=10.0),
            ],
        )
        traj2 = Trajectory(
            vehicle_id="V2",
            vehicle_class="Passenger Car",
            path_id="N-L1_to_S-L1",
            points=[
                _trajpoint(t=5.0, s=0.0, speed_mps=15.0),
                _trajpoint(t=15.0, s=45.0, speed_mps=15.0),
            ],
        )

        samples = compute_macro_samples([traj1, traj2], intersection, interval_s=30.0)

        assert len(samples) > 0
        sample = samples[0]
        assert isinstance(sample, MacroSample)
        assert sample.approach == "N"
        assert sample.density_veh_per_km >= 0.0
        assert sample.speed_kmh >= 0.0
        assert sample.flow_veh_per_hr >= 0.0
        # 2 vehicles in 0.1km approach -> density = 20.0
        assert sample.density_veh_per_km == pytest.approx(20.0)
        # Average speed (10+10+15+15)/4 = 12.5 m/s = 45 km/h
        assert sample.speed_kmh == pytest.approx(45.0)


class TestAverageQueueLength:
    """Verify average_queue_length."""

    def test_queue_flagging_slow_vs_fast(self):
        """Verify slow vehicles near stop line are flagged as queued while fast vehicles are not."""
        intersection = _make_intersection()

        # Slow vehicle near stop line (speed = 1.0 m/s < 2.0 m/s, s = 10.0 <= 50.0)
        traj_slow = Trajectory(
            vehicle_id="V_SLOW",
            vehicle_class="Passenger Car",
            path_id="N-L1_to_S-L1",
            points=[
                _trajpoint(t=0.0, s=10.0, speed_mps=1.0),
            ],
        )

        # Fast vehicle near stop line (speed = 10.0 m/s >= 2.0 m/s, s = 10.0 <= 50.0)
        traj_fast = Trajectory(
            vehicle_id="V_FAST",
            vehicle_class="Passenger Car",
            path_id="N-L1_to_S-L1",
            points=[
                _trajpoint(t=0.0, s=10.0, speed_mps=10.0),
            ],
        )

        # Slow vehicle far from stop line (speed = 1.0 m/s < 2.0 m/s, s = 60.0 > 50.0)
        traj_far = Trajectory(
            vehicle_id="V_FAR",
            vehicle_class="Passenger Car",
            path_id="N-L1_to_S-L1",
            points=[
                _trajpoint(t=0.0, s=60.0, speed_mps=1.0),
            ],
        )

        # Case 1: Slow vehicle near stop line -> queued (1 vehicle * 4.5m = 4.5m)
        q_slow = average_queue_length([traj_slow], intersection, speed_threshold_mps=2.0)
        assert q_slow["N"] == pytest.approx(4.5)

        # Case 2: Fast vehicle near stop line -> not queued (0.0m)
        q_fast = average_queue_length([traj_fast], intersection, speed_threshold_mps=2.0)
        assert q_fast["N"] == pytest.approx(0.0)

        # Case 3: Slow vehicle far from stop line -> not queued (0.0m)
        q_far = average_queue_length([traj_far], intersection, speed_threshold_mps=2.0)
        assert q_far["N"] == pytest.approx(0.0)

"""
Pytest tests for ``engine.evaluation.safety.evaluate_safety``.

All scenarios use hand-constructed fake trajectory data — the physics /
simulation engine is not needed.

Coverage
--------
- ``test_clean_scenario_feasible``: well-spaced vehicles, active signal →
  feasible=True, positive margin.
- ``test_gap_violation_same_path``: two vehicles too close on same path →
  feasible=False, gap violation.
- ``test_signal_violation``: vehicle proceeds during inactive signal phase →
  feasible=False, signal violation.
- ``test_conflict_point_violation``: crossing-path vehicles within unsafe
  time window → feasible=False, conflict-point violation.
- ``test_empty_trajectories``: no trajectories → feasible=True, margin 0.
"""

import pytest

from src.models import (
    Intersection,
    Lane,
    Path,
    PathPoint,
    Signal,
    SignalPhase,
    Trajectory,
    TrajectoryPoint,
)

from engine.evaluation.safety import evaluate_safety


# =============================================================================
# Helpers — minimal model builders
# =============================================================================


def _pathpoint(s: float, x: float, y: float, curvature: float = 0.0) -> PathPoint:
    return PathPoint(s=s, x=x, y=y, curvature=curvature)


def _trajpoint(t: float, s: float, speed_mps: float, accel_mps2: float = 0.0) -> TrajectoryPoint:
    return TrajectoryPoint(t=t, s=s, speed_mps=speed_mps, accel_mps2=accel_mps2)


def _make_intersection(
    paths: list[Path],
    phases: list[SignalPhase],
    cycle_s: float = 120.0,
) -> Intersection:
    """Build a minimal Intersection with sane defaults for lanes / signal."""
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
        Lane(
            id="E-L1",
            approach="E",
            width_m=3.5,
            allowed_movements=["through", "left"],
            vehicle_classes=["Passenger Car"],
        ),
        Lane(
            id="W-L1",
            approach="W",
            width_m=3.5,
            allowed_movements=["through", "left"],
            vehicle_classes=["Passenger Car"],
        ),
    ]
    signal = Signal(
        id="SIG-1",
        cycle_s=cycle_s,
        phases=phases,
    )
    return Intersection(
        id="INT-1",
        name="Test Intersection",
        lanes=lanes,
        paths=paths,
        signal=signal,
    )


# =============================================================================
# Shared fixtures
# =============================================================================


@pytest.fixture()
def straight_path_ns() -> Path:
    """A straight north-to-south path, 20 m long."""
    return Path(
        id="P-NS",
        entry_lane_id="N-L1",
        exit_lane_id="S-L1",
        movement="through",
        points=[
            _pathpoint(s=0.0, x=0.0, y=10.0),
            _pathpoint(s=10.0, x=0.0, y=0.0),
            _pathpoint(s=20.0, x=0.0, y=-10.0),
        ],
        speed_limit_mps=11.1,
    )


@pytest.fixture()
def crossing_path_ew() -> Path:
    """An east-to-west path that geometrically crosses the N-S path at origin."""
    return Path(
        id="P-EW",
        entry_lane_id="E-L1",
        exit_lane_id="W-L1",
        movement="through",
        points=[
            _pathpoint(s=0.0, x=10.0, y=0.0),
            _pathpoint(s=10.0, x=0.0, y=0.0),   # crosses N-S mid-point
            _pathpoint(s=20.0, x=-10.0, y=0.0),
        ],
        speed_limit_mps=11.1,
    )


@pytest.fixture()
def green_phase_ns() -> SignalPhase:
    """Phase with P-NS active for 60 s."""
    return SignalPhase(id="P1", active_movement_ids=["P-NS"], duration_s=60.0)


@pytest.fixture()
def green_phase_ew() -> SignalPhase:
    """Phase with P-EW active for 60 s."""
    return SignalPhase(id="P2", active_movement_ids=["P-EW"], duration_s=60.0)


# =============================================================================
# Test: clean scenario — well-spaced, correct signal → feasible
# =============================================================================


class TestCleanScenario:
    """All vehicles spaced safely apart and proceeding on active green."""

    def test_clean_scenario_feasible(
        self, straight_path_ns: Path, green_phase_ns: SignalPhase, green_phase_ew: SignalPhase,
    ):
        intersection = _make_intersection(
            paths=[straight_path_ns],
            phases=[green_phase_ns, green_phase_ew],
        )

        # Two vehicles on same path but well separated (10 m gap, speed = 10 m/s
        # → required = max(0.5*10, 2) = 5 m, so 10 m gap is fine).
        traj_a = Trajectory(
            vehicle_id="V1",
            vehicle_class="Passenger Car",
            path_id="P-NS",
            points=[
                _trajpoint(t=0.0, s=0.0, speed_mps=10.0),
                _trajpoint(t=1.0, s=10.0, speed_mps=10.0),
                _trajpoint(t=2.0, s=20.0, speed_mps=10.0),
            ],
        )
        traj_b = Trajectory(
            vehicle_id="V2",
            vehicle_class="Passenger Car",
            path_id="P-NS",
            points=[
                _trajpoint(t=1.0, s=0.0, speed_mps=10.0),
                _trajpoint(t=2.0, s=10.0, speed_mps=10.0),
                _trajpoint(t=3.0, s=20.0, speed_mps=10.0),
            ],
        )

        result = evaluate_safety(intersection, [traj_a, traj_b])

        assert result.feasible is True
        assert result.margin > 0
        assert result.violations == []
        assert result.intersection_id == "INT-1"


# =============================================================================
# Test: gap violation — two vehicles too close on same path
# =============================================================================


class TestGapViolation:
    """Two vehicles on the same path with insufficient following distance."""

    def test_gap_violation_same_path(
        self, straight_path_ns: Path, green_phase_ns: SignalPhase, green_phase_ew: SignalPhase,
    ):
        intersection = _make_intersection(
            paths=[straight_path_ns],
            phases=[green_phase_ns, green_phase_ew],
        )

        # Both vehicles at overlapping positions at t=1.0:
        # V1 at s=10, V2 at s=9 → gap = 1 m.  At speed 10 m/s the required
        # gap is max(0.5*10, 2) = 5 m → violation of 4 m.
        traj_a = Trajectory(
            vehicle_id="V1",
            vehicle_class="Passenger Car",
            path_id="P-NS",
            points=[
                _trajpoint(t=0.0, s=0.0, speed_mps=10.0),
                _trajpoint(t=1.0, s=10.0, speed_mps=10.0),
            ],
        )
        traj_b = Trajectory(
            vehicle_id="V2",
            vehicle_class="Passenger Car",
            path_id="P-NS",
            points=[
                _trajpoint(t=0.0, s=0.5, speed_mps=10.0),
                _trajpoint(t=1.0, s=9.0, speed_mps=10.0),
            ],
        )

        result = evaluate_safety(intersection, [traj_a, traj_b])

        assert result.feasible is False
        assert result.margin < 0
        # At least one violation should mention "Gap violation"
        assert any("Gap violation" in v for v in result.violations)


# =============================================================================
# Test: signal violation — vehicle proceeds on red
# =============================================================================


class TestSignalViolation:
    """Vehicle enters intersection while its path has no active green."""

    def test_signal_violation(
        self, straight_path_ns: Path, green_phase_ew: SignalPhase,
    ):
        # Only P-EW is green; P-NS is never active.
        intersection = _make_intersection(
            paths=[straight_path_ns],
            phases=[green_phase_ew],
            cycle_s=60.0,
        )

        traj = Trajectory(
            vehicle_id="V-RED",
            vehicle_class="Passenger Car",
            path_id="P-NS",
            points=[
                _trajpoint(t=5.0, s=0.0, speed_mps=8.0),
                _trajpoint(t=6.0, s=8.0, speed_mps=8.0),
            ],
        )

        result = evaluate_safety(intersection, [traj])

        assert result.feasible is False
        assert result.margin < 0
        assert any("Signal violation" in v for v in result.violations)


# =============================================================================
# Test: conflict-point violation — crossing paths unsafe time gap
# =============================================================================


class TestConflictPointViolation:
    """Vehicles on crossing paths pass the shared zone within unsafe time."""

    def test_conflict_point_violation(
        self,
        straight_path_ns: Path,
        crossing_path_ew: Path,
        green_phase_ns: SignalPhase,
        green_phase_ew: SignalPhase,
    ):
        # Both paths green simultaneously for simplicity (signal won't fire).
        combined_phase = SignalPhase(
            id="P-ALL", active_movement_ids=["P-NS", "P-EW"], duration_s=120.0,
        )
        intersection = _make_intersection(
            paths=[straight_path_ns, crossing_path_ew],
            phases=[combined_phase],
        )

        # Both vehicles reach the crossing zone (s=10 for both paths, which
        # maps to (0,0)) at nearly the same time: t≈1.0 s vs t≈1.2 s → gap
        # of 0.2 s, well under 1.5 s threshold.
        traj_ns = Trajectory(
            vehicle_id="V-NS",
            vehicle_class="Passenger Car",
            path_id="P-NS",
            points=[
                _trajpoint(t=0.0, s=0.0, speed_mps=10.0),
                _trajpoint(t=1.0, s=10.0, speed_mps=10.0),
                _trajpoint(t=2.0, s=20.0, speed_mps=10.0),
            ],
        )
        traj_ew = Trajectory(
            vehicle_id="V-EW",
            vehicle_class="Passenger Car",
            path_id="P-EW",
            points=[
                _trajpoint(t=0.0, s=0.0, speed_mps=10.0),
                _trajpoint(t=1.2, s=10.0, speed_mps=10.0),
                _trajpoint(t=2.4, s=20.0, speed_mps=10.0),
            ],
        )

        result = evaluate_safety(intersection, [traj_ns, traj_ew])

        assert result.feasible is False
        assert result.margin < 0
        assert any("Conflict point" in v for v in result.violations)


# =============================================================================
# Test: empty trajectories — trivially safe
# =============================================================================


class TestEdgeCases:
    """Edge-case inputs that should not crash."""

    def test_empty_trajectories(
        self, straight_path_ns: Path, green_phase_ns: SignalPhase, green_phase_ew: SignalPhase,
    ):
        intersection = _make_intersection(
            paths=[straight_path_ns],
            phases=[green_phase_ns, green_phase_ew],
        )

        result = evaluate_safety(intersection, [])

        assert result.feasible is True
        assert result.margin == 0.0
        assert result.violations == []

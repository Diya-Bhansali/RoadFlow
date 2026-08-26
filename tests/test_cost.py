"""
Pytest tests for ``engine.evaluation.cost.estimate_cost``.

Coverage
--------
- ``test_canonical_positive_cost``: canonical_4arm scenario returns a positive float.
- ``test_more_lanes_higher_cost``: an intersection with more lanes produces a
  strictly higher cost than one with fewer lanes.
- ``test_zero_curves_no_crash``: an intersection where all paths are straight
  (curvature = 0 everywhere) runs without error.
"""

import pytest

from src.models import (
    Intersection,
    Lane,
    Path,
    PathPoint,
    Signal,
    SignalPhase,
)

from engine.evaluation.cost import estimate_cost
from scenarios.canonical_4arm import INTERSECTION as CANONICAL


# =============================================================================
# Helpers
# =============================================================================


def _pathpoint(s: float, x: float, y: float, curvature: float = 0.0) -> PathPoint:
    return PathPoint(s=s, x=x, y=y, curvature=curvature)


def _straight_path(
    id: str,
    entry: str = "N-L1",
    exit: str = "S-L1",
) -> Path:
    """A simple straight path with zero curvature."""
    return Path(
        id=id,
        entry_lane_id=entry,
        exit_lane_id=exit,
        movement="through",
        points=[
            _pathpoint(s=0.0, x=0.0, y=10.0),
            _pathpoint(s=20.0, x=0.0, y=-10.0),
        ],
        speed_limit_mps=11.1,
    )


def _make_intersection(
    num_lanes: int,
    paths: list[Path] | None = None,
    phases: list[SignalPhase] | None = None,
) -> Intersection:
    """Build a minimal Intersection with *num_lanes* lanes.

    Extra lanes beyond 4 are added on the N and S approaches.
    """
    approaches = ["N", "S", "E", "W"]
    lanes: list[Lane] = []
    for i in range(num_lanes):
        ap = approaches[i % len(approaches)]
        lanes.append(
            Lane(
                id=f"{ap}-L{i + 1}",
                approach=ap,
                width_m=3.5,
                allowed_movements=["through"],
                vehicle_classes=["Passenger Car"],
            )
        )

    if paths is None:
        paths = [_straight_path("P-default")]
    if phases is None:
        phases = [
            SignalPhase(id="P1", active_movement_ids=["P-default"], duration_s=60.0),
        ]

    return Intersection(
        id="INT-TEST",
        name="Test Intersection",
        lanes=lanes,
        paths=paths,
        signal=Signal(id="SIG-TEST", cycle_s=120.0, phases=phases),
    )


# =============================================================================
# Tests
# =============================================================================


class TestCanonicalScenario:
    """Verify estimate_cost on the canonical_4arm scenario."""

    def test_canonical_positive_cost(self):
        """Verify canonical intersection returns positive cost estimate."""
        cost = estimate_cost(CANONICAL)

        assert isinstance(cost, float)
        assert cost > 0

    def test_canonical_cost_includes_lane_and_phase_terms(self):
        """Sanity-check: canonical has 12 lanes and 4 phases, so cost should
        exceed BASE + 12*LANE + 4*PHASE = 500k + 1800k + 80k = 2380k."""
        cost = estimate_cost(CANONICAL)
        assert cost > 2_380_000


class TestLaneCountComparison:
    """More lanes → higher cost, all else being equal."""

    def test_more_lanes_higher_cost(self):
        """Verify intersections with more lanes have higher estimated cost."""
        fewer = _make_intersection(num_lanes=4)
        more = _make_intersection(num_lanes=8)

        cost_fewer = estimate_cost(fewer)
        cost_more = estimate_cost(more)

        assert cost_more > cost_fewer


class TestZeroCurves:
    """All-straight paths should not crash or produce NaN."""

    def test_zero_curves_no_crash(self):
        """Verify intersections with only straight paths do not crash cost estimation."""
        ix = _make_intersection(
            num_lanes=4,
            paths=[_straight_path("P-straight")],
        )

        cost = estimate_cost(ix)

        assert isinstance(cost, float)
        assert cost > 0
        # With zero curves, curve term = 0.  Cost should equal
        # BASE + 4*LANE + 1*PHASE = 500k + 600k + 20k = 1_120_000.
        assert cost == pytest.approx(1_120_000.0)

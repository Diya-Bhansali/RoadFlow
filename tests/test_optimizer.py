"""
Pytest tests for ``engine.optimization.optimizer``.

Coverage
--------
- ``test_grid_search_completion_and_ranking``: grid search completes, returns
  a ranked list sorted by score, and marks the top result as recommended.
- ``test_infeasible_designs_filtered``: all results returned in the ranked list
  are feasible.
- ``test_optimization_execution_time``: confirms optimization completes well
  under the 10-second requirement.
"""

import time

import pytest

from engine.optimization.optimizer import (
    build_modified_intersection,
    run_optimization,
)
from scenarios.canonical_4arm import INTERSECTION as CANONICAL_INTERSECTION
from src.models import SafetyResult


def test_grid_search_completion_and_ranking():
    start_time = time.time()
    results = run_optimization(CANONICAL_INTERSECTION)
    elapsed = time.time() - start_time

    assert len(results) > 0
    assert elapsed < 10.0

    # Top result should be recommended
    assert results[0]["recommended"] is True

    # Remaining results should not be recommended
    for r in results[1:]:
        assert r["recommended"] is False

    # Scores should be sorted ascending (lower is better)
    scores = [r["score"] for r in results]
    assert scores == sorted(scores)


def test_infeasible_designs_filtered():
    results = run_optimization(CANONICAL_INTERSECTION)

    for r in results:
        safety_res: SafetyResult = r["safety_result"]
        assert safety_res.feasible is True
        assert r["feasible"] is True


def test_optimization_execution_time():
    start_time = time.time()
    results = run_optimization(CANONICAL_INTERSECTION)
    elapsed = time.time() - start_time

    # Must complete in under 10 seconds
    assert elapsed < 10.0
    assert len(results) == 27  # 3 lane_counts * 3 signal_splits * 3 curve_radii


def test_build_modified_intersection():
    modified = build_modified_intersection(
        CANONICAL_INTERSECTION, lane_count=4, signal_split=[40, 20, 40, 20], curve_radius=12.0
    )

    assert len(modified.lanes) == 16  # 4 approaches * 4 lanes
    assert modified.signal.cycle_s == 120.0
    assert len(modified.signal.phases) == 4
    assert modified.signal.phases[0].duration_s == 40.0

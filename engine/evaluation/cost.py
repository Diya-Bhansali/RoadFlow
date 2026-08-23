"""
Cost estimation engine for RoadFlow intersection designs.

Provides ``estimate_cost`` — a formula-based cost estimator that derives a
rough construction cost from the static intersection geometry and signal
configuration.  No trajectory or simulation data is needed.

Formula
-------
::

    cost = BASE_COST
         + total_lane_count  × COST_PER_LANE
         + Σ (radius_i)      × COST_PER_METER_RADIUS   (for curved path points)
         + num_signal_phases  × COST_PER_PHASE

.. note::

   The per-unit cost constants are **placeholders**.  They should be replaced
   with regionally calibrated values once real construction cost data is
   available.
"""

from __future__ import annotations

import math

from src.models import Intersection

# ---------------------------------------------------------------------------
# Placeholder cost assumptions  (documented as such — no real data yet)
# ---------------------------------------------------------------------------

BASE_COST: float = 500_000
"""Fixed base cost for intersection construction (INR / generic currency)."""

COST_PER_LANE: float = 150_000
"""Incremental cost per lane across all approaches."""

COST_PER_METER_RADIUS: float = 8_000
"""Incremental cost per metre of curve radius for each curved path point.
Captures the additional engineering required for turn channelisation,
kerb radii, and super-elevation.  Applied once per curved path point
(``PathPoint.curvature != 0``)."""

COST_PER_PHASE: float = 20_000
"""Incremental cost per signal phase (controller hardware, detection, wiring)."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def estimate_cost(intersection: Intersection) -> float:
    """Estimate the construction cost of an intersection design.

    Parameters
    ----------
    intersection:
        A fully specified ``Intersection`` model (lanes, paths, signal).

    Returns
    -------
    float
        Estimated cost in abstract currency units (positive).

    Notes
    -----
    Curvature is defined as ``1 / radius`` in ``PathPoint``.  Points with
    ``curvature == 0`` represent straight segments and are excluded from the
    curve cost term.
    """
    # 1. Lane cost
    total_lane_count = len(intersection.lanes)

    # 2. Curve cost — collect radii from all curved path points
    curve_radii: list[float] = []
    for path in intersection.paths:
        for pt in path.points:
            if not math.isclose(pt.curvature, 0.0):
                radius = abs(1.0 / pt.curvature)
                curve_radii.append(radius)

    num_curves = len(curve_radii)
    avg_radius = (sum(curve_radii) / num_curves) if num_curves > 0 else 0.0

    # 3. Signal phase cost
    num_signal_phases = len(intersection.signal.phases)

    # 4. Assemble total
    cost = (
        BASE_COST
        + total_lane_count * COST_PER_LANE
        + avg_radius * COST_PER_METER_RADIUS * num_curves
        + num_signal_phases * COST_PER_PHASE
    )

    return cost

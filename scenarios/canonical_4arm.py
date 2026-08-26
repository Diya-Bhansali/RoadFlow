"""
Canonical 4-arm signalised intersection scenario for RoadFlow.

Geometry
--------
A symmetric at-grade 4-way intersection with:
  - 4 approaches: N, S, E, W
  - 3 lanes per approach: L1 (left-turn), L2 (through), L3 (right-turn)
  - Straight-line path approximations through a 40 m x 40 m box
  - 12 paths total: 4 through + 4 left-turn + 4 right-turn

Signal
------
4-phase, 120 s cycle with equal 30 s splits:
  P1 — NS through + right   (non-conflicting pair)
  P2 — EW through + right
  P3 — NS left turns
  P4 — EW left turns

Demand
------
36 DemandRecord rows: 4 approaches x 3 movements x 3 vehicle classes.
Vehicle classes: Passenger Car, Two-Wheeler, Auto-Rickshaw.
Flow rates are representative urban peak-hour values.

Usage
-----
    from scenarios.canonical_4arm import INTERSECTION, DEMAND_RECORDS
"""

from __future__ import annotations

import math

from src.models import (
    DemandRecord,
    Intersection,
    Lane,
    Path,
    PathPoint,
    Signal,
    SignalPhase,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HALF_BOX = 10.0       # Half the intersection box side (box = 20 m x 20 m)
RUN_OUT = 30.0        # Distance from box edge to lane start/end
LANE_WIDTH = 3.5      # metres

SPEED_THROUGH = 11.1  # m/s ≈ 40 km/h
SPEED_TURN = 5.0      # m/s ≈ 18 km/h

VEHICLE_CLASSES = ["Passenger Car", "Two-Wheeler", "Auto-Rickshaw"]
APPROACHES = ["N", "S", "E", "W"]

# ---------------------------------------------------------------------------
# Coordinate origin = centre of intersection box.
#
# For N/S approaches:  x is the lateral offset, y is the longitudinal axis.
# For E/W approaches:  y is the lateral offset, x is the longitudinal axis.
#
# Lane lateral offsets from centreline (driver's left is negative):
#   L1 (left-turn):   lateral = -LANE_WIDTH
#   L2 (through):     lateral = 0
#   L3 (right-turn):  lateral = +LANE_WIDTH
# ---------------------------------------------------------------------------

def _points_straight(
    x0: float, y0: float, x1: float, y1: float, n: int = 5
) -> list[PathPoint]:
    """Return n evenly-spaced PathPoints along a straight line; curvature = 0."""
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


def _points_turn(
    x0: float,
    y0: float,
    xm: float,
    ym: float,
    x1: float,
    y1: float,
    curvature: float = 0.05,
) -> list[PathPoint]:
    """
    Three-point turning-path approximation: entry -> pivot -> exit.
    The pivot point carries a small constant curvature; entry and exit are 0.
    """
    leg1 = math.sqrt((xm - x0) ** 2 + (ym - y0) ** 2)
    leg2 = math.sqrt((x1 - xm) ** 2 + (y1 - ym) ** 2)
    total = leg1 + leg2
    return [
        PathPoint(s=0.0,   x=x0, y=y0, curvature=0.0),
        PathPoint(s=leg1,  x=xm, y=ym, curvature=curvature),
        PathPoint(s=total, x=x1, y=y1, curvature=0.0),
    ]


# Approach stop-line positions (at box edge) and run-out positions
#   N approach: vehicles travel from +y towards -y (southward through box)
_NS_STOP = HALF_BOX
_NS_EXIT = -(HALF_BOX + RUN_OUT)
_NS_ENTRY = HALF_BOX + RUN_OUT

_EW_STOP = HALF_BOX
_EW_EXIT = -(HALF_BOX + RUN_OUT)
_EW_ENTRY = HALF_BOX + RUN_OUT

# Lateral offsets
_N_OFF = {"L1": -LANE_WIDTH, "L2": 0.0, "L3": LANE_WIDTH}
_S_OFF = {"L1":  LANE_WIDTH, "L2": 0.0, "L3": -LANE_WIDTH}   # heading N: mirrored
_E_OFF = {"L1":  LANE_WIDTH, "L2": 0.0, "L3": -LANE_WIDTH}
_W_OFF = {"L1": -LANE_WIDTH, "L2": 0.0, "L3":  LANE_WIDTH}


# ---------------------------------------------------------------------------
# 1. Lanes — 4 approaches × 3 lanes = 12 lanes
# ---------------------------------------------------------------------------

LANES: list[Lane] = [
    Lane(id=f"{ap}-{lk}", approach=ap, width_m=LANE_WIDTH,
         allowed_movements=[mv], vehicle_classes=VEHICLE_CLASSES)
    for ap, lk, mv in [
        ("N", "L1", "left"),    ("N", "L2", "through"), ("N", "L3", "right"),
        ("S", "L1", "left"),    ("S", "L2", "through"), ("S", "L3", "right"),
        ("E", "L1", "left"),    ("E", "L2", "through"), ("E", "L3", "right"),
        ("W", "L1", "left"),    ("W", "L2", "through"), ("W", "L3", "right"),
    ]
]


# ---------------------------------------------------------------------------
# 2. Paths — 12 paths (4 through + 4 left + 4 right)
#
#    Naming convention: <entry_lane_id>_to_<exit_lane_id>
#
#    Through:  N→S, S→N, E→W, W→E   (straight across)
#    Left:     N→E, S→W, E→S, W→N   (cross-traffic left in Indian LHT)
#    Right:    N→W, S→E, E→N, W→S   (near-side right turn)
# ---------------------------------------------------------------------------

def _build_paths() -> list[Path]:
    paths: list[Path] = []

    # ---- THROUGH -----------------------------------------------------------
    # N-L2  →  S-L2
    paths.append(Path(
        id="N-L2_to_S-L2", entry_lane_id="N-L2", exit_lane_id="S-L2",
        movement="through",
        points=_points_straight(_N_OFF["L2"], _NS_ENTRY,  _S_OFF["L2"], _NS_EXIT),
        speed_limit_mps=SPEED_THROUGH,
    ))
    # S-L2  →  N-L2
    paths.append(Path(
        id="S-L2_to_N-L2", entry_lane_id="S-L2", exit_lane_id="N-L2",
        movement="through",
        points=_points_straight(_S_OFF["L2"], -_NS_ENTRY, _N_OFF["L2"], -_NS_EXIT),
        speed_limit_mps=SPEED_THROUGH,
    ))
    # E-L2  →  W-L2
    paths.append(Path(
        id="E-L2_to_W-L2", entry_lane_id="E-L2", exit_lane_id="W-L2",
        movement="through",
        points=_points_straight(_EW_ENTRY, _E_OFF["L2"], _EW_EXIT, _W_OFF["L2"]),
        speed_limit_mps=SPEED_THROUGH,
    ))
    # W-L2  →  E-L2
    paths.append(Path(
        id="W-L2_to_E-L2", entry_lane_id="W-L2", exit_lane_id="E-L2",
        movement="through",
        points=_points_straight(-_EW_ENTRY, _W_OFF["L2"], -_EW_EXIT, _E_OFF["L2"]),
        speed_limit_mps=SPEED_THROUGH,
    ))

    # ---- LEFT --------------------------------------------------------------
    # N-L1  →  E-L1  (N approach turns left, exits east)
    paths.append(Path(
        id="N-L1_to_E-L1", entry_lane_id="N-L1", exit_lane_id="E-L1",
        movement="left",
        points=_points_turn(
            _N_OFF["L1"], _NS_ENTRY,
            -HALF_BOX / 2, HALF_BOX / 2,
            _EW_EXIT, _E_OFF["L1"],
        ),
        speed_limit_mps=SPEED_TURN,
    ))
    # S-L1  →  W-L1
    paths.append(Path(
        id="S-L1_to_W-L1", entry_lane_id="S-L1", exit_lane_id="W-L1",
        movement="left",
        points=_points_turn(
            _S_OFF["L1"], -_NS_ENTRY,
            HALF_BOX / 2, -HALF_BOX / 2,
            -_EW_EXIT, _W_OFF["L1"],
        ),
        speed_limit_mps=SPEED_TURN,
    ))
    # E-L1  →  S-L1
    paths.append(Path(
        id="E-L1_to_S-L1", entry_lane_id="E-L1", exit_lane_id="S-L1",
        movement="left",
        points=_points_turn(
            _EW_ENTRY, _E_OFF["L1"],
            HALF_BOX / 2, HALF_BOX / 2,
            _S_OFF["L1"], _NS_EXIT,
        ),
        speed_limit_mps=SPEED_TURN,
    ))
    # W-L1  →  N-L1
    paths.append(Path(
        id="W-L1_to_N-L1", entry_lane_id="W-L1", exit_lane_id="N-L1",
        movement="left",
        points=_points_turn(
            -_EW_ENTRY, _W_OFF["L1"],
            -HALF_BOX / 2, -HALF_BOX / 2,
            _N_OFF["L1"], -_NS_EXIT,
        ),
        speed_limit_mps=SPEED_TURN,
    ))

    # ---- RIGHT -------------------------------------------------------------
    # N-L3  →  W-L3
    paths.append(Path(
        id="N-L3_to_W-L3", entry_lane_id="N-L3", exit_lane_id="W-L3",
        movement="right",
        points=_points_turn(
            _N_OFF["L3"], _NS_ENTRY,
            HALF_BOX / 2, HALF_BOX / 2,
            -_EW_EXIT, _W_OFF["L3"],
        ),
        speed_limit_mps=SPEED_TURN,
    ))
    # S-L3  →  E-L3
    paths.append(Path(
        id="S-L3_to_E-L3", entry_lane_id="S-L3", exit_lane_id="E-L3",
        movement="right",
        points=_points_turn(
            _S_OFF["L3"], -_NS_ENTRY,
            -HALF_BOX / 2, -HALF_BOX / 2,
            _EW_EXIT, _E_OFF["L3"],
        ),
        speed_limit_mps=SPEED_TURN,
    ))
    # E-L3  →  N-L3
    paths.append(Path(
        id="E-L3_to_N-L3", entry_lane_id="E-L3", exit_lane_id="N-L3",
        movement="right",
        points=_points_turn(
            _EW_ENTRY, _E_OFF["L3"],
            HALF_BOX / 2, -HALF_BOX / 2,
            _N_OFF["L3"], -_NS_EXIT,
        ),
        speed_limit_mps=SPEED_TURN,
    ))
    # W-L3  →  S-L3
    paths.append(Path(
        id="W-L3_to_S-L3", entry_lane_id="W-L3", exit_lane_id="S-L3",
        movement="right",
        points=_points_turn(
            -_EW_ENTRY, _W_OFF["L3"],
            -HALF_BOX / 2, HALF_BOX / 2,
            _S_OFF["L3"], _NS_EXIT,
        ),
        speed_limit_mps=SPEED_TURN,
    ))

    return paths


PATHS: list[Path] = _build_paths()


# ---------------------------------------------------------------------------
# 3. Signal — 4 phases, 30 s each, 120 s cycle
#
#    Phase timing matches the 30-30-30-30 split referenced in SPEC.md
#    data-contract timing example.
#
#    P1: NS through + NS right  (simultaneous; no cross-conflict)
#    P2: EW through + EW right
#    P3: NS left turns          (protected; conflicts cleared by P1/P2 gaps)
#    P4: EW left turns
# ---------------------------------------------------------------------------

SIGNAL = Signal(
    id="SIG-CANONICAL-4ARM",
    cycle_s=120.0,
    phases=[
        SignalPhase(
            id="P1",
            active_movement_ids=["N-L2_to_S-L2", "S-L2_to_N-L2",
                                  "N-L3_to_W-L3", "S-L3_to_E-L3"],
            duration_s=30.0,
        ),
        SignalPhase(
            id="P2",
            active_movement_ids=["E-L2_to_W-L2", "W-L2_to_E-L2",
                                  "E-L3_to_N-L3", "W-L3_to_S-L3"],
            duration_s=30.0,
        ),
        SignalPhase(
            id="P3",
            active_movement_ids=["N-L1_to_E-L1", "S-L1_to_W-L1"],
            duration_s=30.0,
        ),
        SignalPhase(
            id="P4",
            active_movement_ids=["E-L1_to_S-L1", "W-L1_to_N-L1"],
            duration_s=30.0,
        ),
    ],
)


# ---------------------------------------------------------------------------
# 4. Intersection assembly
# ---------------------------------------------------------------------------

INTERSECTION = Intersection(
    id="INT-CANONICAL-4ARM",
    name="Canonical 4-Arm Signalised Intersection",
    lanes=LANES,
    paths=PATHS,
    signal=SIGNAL,
    city="Pune, Maharashtra",
    control_type="Pre-Timed Signal",
    coord_system="WGS 84",
    lat=18.5074,
    lng=73.8077,
)


# ---------------------------------------------------------------------------
# 5. Demand records — 4 approaches × 3 movements × 3 vehicle classes = 36 rows
#
#    Representative peak-hour flows (veh/hr):
#
#    Class            | through | left | right
#    -----------------|---------|------|------
#    Passenger Car    |   300   |  150 |  120
#    Two-Wheeler      |   500   |  200 |  180
#    Auto-Rickshaw    |   150   |   80 |   60
# ---------------------------------------------------------------------------

_DEMAND_TABLE: dict[tuple[str, str], float] = {
    ("Passenger Car", "through"): 300.0,
    ("Passenger Car", "left"):    150.0,
    ("Passenger Car", "right"):   120.0,
    ("Two-Wheeler",   "through"): 500.0,
    ("Two-Wheeler",   "left"):    200.0,
    ("Two-Wheeler",   "right"):   180.0,
    ("Auto-Rickshaw", "through"): 150.0,
    ("Auto-Rickshaw", "left"):     80.0,
    ("Auto-Rickshaw", "right"):    60.0,
}

DEMAND_RECORDS: list[DemandRecord] = [
    DemandRecord(
        approach=approach,
        movement=movement,
        vehicle_class=vc,
        vehicles_per_hour=vph,
    )
    for approach in APPROACHES
    for (vc, movement), vph in _DEMAND_TABLE.items()
]


# ---------------------------------------------------------------------------
# Quick self-check when executed directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"Intersection : {INTERSECTION.id!r}")
    print(f"Name         : {INTERSECTION.name!r}")
    print(f"Lanes        : {len(INTERSECTION.lanes)}")
    print(f"Paths        : {len(INTERSECTION.paths)}")
    print(f"Phases       : {len(INTERSECTION.signal.phases)}")
    print(f"Cycle        : {INTERSECTION.signal.cycle_s} s")
    print(f"Demand rows  : {len(DEMAND_RECORDS)}")
    for ph in INTERSECTION.signal.phases:
        print(f"  {ph.id}  {ph.duration_s}s  → {ph.active_movement_ids}")

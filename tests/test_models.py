"""
Pytest unit tests for src/models.py.

Coverage
--------
- Each model can be instantiated with valid data.
- At least one validation constraint is exercised per model (ValidationError
  is raised when the constraint is violated).
"""

import pytest
from pydantic import ValidationError

from src.models import (
    DemandRecord,
    Intersection,
    Lane,
    MacroSample,
    Path,
    PathPoint,
    SafetyResult,
    Signal,
    SignalPhase,
    Trajectory,
    TrajectoryPoint,
    Vehicle,
)


# =============================================================================
# Helpers
# =============================================================================

def _pp(s=0.0, x=0.0, y=0.0, curvature=0.0) -> dict:
    return {"s": s, "x": x, "y": y, "curvature": curvature}


def _lane(id="N-L1", approach="N", width_m=3.5, movements=None, classes=None) -> dict:
    return {
        "id": id,
        "approach": approach,
        "width_m": width_m,
        "allowed_movements": movements or ["through"],
        "vehicle_classes": classes or ["Passenger Car"],
    }


def _path(id="P-NS", entry="N-L2", exit="S-L2", movement="through", speed=11.1) -> dict:
    return {
        "id": id,
        "entry_lane_id": entry,
        "exit_lane_id": exit,
        "movement": movement,
        "points": [_pp(0.0, 0.0, 10.0), _pp(20.0, 0.0, -10.0)],
        "speed_limit_mps": speed,
    }


def _phase(id="P1", movements=None, duration_s=30.0) -> dict:
    return {"id": id, "active_movement_ids": movements or ["P-NS"], "duration_s": duration_s}


def _signal() -> dict:
    return {
        "id": "SIG-1",
        "cycle_s": 120.0,
        "phases": [
            _phase("P1", ["P-NS"], 30.0),
            _phase("P2", ["P-EW"], 30.0),
            _phase("P3", ["P-NS-L"], 30.0),
            _phase("P4", ["P-EW-L"], 30.0),
        ],
    }


# =============================================================================
# Vehicle  (existing model — original tests preserved)
# =============================================================================

def test_vehicle_instantiation_by_alias():
    data = {"class": "Passenger Car", "length": 4.5,
            "max_accel": 2.5, "max_decel": 4.5, "desired_speed": 15.0}
    v = Vehicle(**data)
    assert v.vehicle_class == "Passenger Car"
    assert v.length == 4.5
    assert v.max_accel == 2.5
    assert v.max_decel == 4.5
    assert v.desired_speed == 15.0


def test_vehicle_instantiation_by_name():
    v = Vehicle(vehicle_class="Two-Wheeler", length=1.8,
                max_accel=3.5, max_decel=5.0, desired_speed=12.0)
    assert v.vehicle_class == "Two-Wheeler"
    assert v.length == 1.8


def test_vehicle_validation_errors():
    with pytest.raises(ValidationError):       # missing fields
        Vehicle(length=4.5)
    with pytest.raises(ValidationError):       # length = 0
        Vehicle(vehicle_class="Auto-rickshaw", length=0,
                max_accel=1.5, max_decel=2.0, desired_speed=9.0)
    with pytest.raises(ValidationError):       # negative max_accel
        Vehicle(vehicle_class="Auto-rickshaw", length=2.5,
                max_accel=-1.0, max_decel=2.0, desired_speed=9.0)


def test_vehicle_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        Vehicle(**{"class": "Passenger Car", "length": 4.5,
                   "max_accel": 2.5, "max_decel": 4.5,
                   "desired_speed": 15.0, "extra_field": "no"})


def test_vehicle_serialization():
    v = Vehicle(vehicle_class="Passenger Car", length=4.5,
                max_accel=2.5, max_decel=4.5, desired_speed=15.0)
    s = v.model_dump(by_alias=True)
    assert "class" in s
    assert s["class"] == "Passenger Car"
    assert s["length"] == 4.5


# =============================================================================
# Lane
# =============================================================================

def test_lane_valid():
    l = Lane(**_lane("N-L1", approach="N", width_m=3.5, movements=["through", "left"]))
    assert l.id == "N-L1"
    assert l.approach == "N"
    assert l.width_m == 3.5
    assert "through" in l.allowed_movements


def test_lane_all_four_approaches():
    for ap in ("N", "S", "E", "W"):
        l = Lane(**_lane(f"{ap}-L1", approach=ap))
        assert l.approach == ap


def test_lane_invalid_approach():
    with pytest.raises(ValidationError):
        Lane(**{**_lane(), "approach": "X"})


def test_lane_width_zero_rejected():
    with pytest.raises(ValidationError):
        Lane(**_lane(width_m=0))


def test_lane_width_negative_rejected():
    with pytest.raises(ValidationError):
        Lane(**_lane(width_m=-2.0))


def test_lane_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        Lane(**{**_lane(), "bogus": True})


# =============================================================================
# PathPoint
# =============================================================================

def test_path_point_valid():
    pp = PathPoint(s=5.0, x=1.0, y=2.0, curvature=0.05)
    assert pp.s == 5.0
    assert pp.curvature == 0.05


def test_path_point_negative_curvature_allowed():
    """Curvature is a signed quantity; negative values are geometrically valid."""
    pp = PathPoint(s=10.0, x=0.0, y=0.0, curvature=-0.02)
    assert pp.curvature == -0.02


def test_path_point_zero_curvature_allowed():
    pp = PathPoint(s=0.0, x=0.0, y=0.0, curvature=0.0)
    assert pp.curvature == 0.0


# =============================================================================
# Path
# =============================================================================

def test_path_valid():
    p = Path(**_path())
    assert p.id == "P-NS"
    assert p.movement == "through"
    assert len(p.points) == 2
    assert p.speed_limit_mps == 11.1


def test_path_speed_zero_rejected():
    with pytest.raises(ValidationError):
        Path(**_path(speed=0))


def test_path_speed_negative_rejected():
    with pytest.raises(ValidationError):
        Path(**_path(speed=-5.0))


def test_path_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        Path(**{**_path(), "extra": "bad"})


# =============================================================================
# SignalPhase
# =============================================================================

def test_signal_phase_valid():
    sp = SignalPhase(**_phase("P1", ["P-NS"], 30.0))
    assert sp.id == "P1"
    assert sp.duration_s == 30.0


def test_signal_phase_zero_duration_rejected():
    with pytest.raises(ValidationError):
        SignalPhase(**_phase(duration_s=0))


def test_signal_phase_negative_duration_rejected():
    with pytest.raises(ValidationError):
        SignalPhase(**_phase(duration_s=-10.0))


# =============================================================================
# Signal
# =============================================================================

def test_signal_valid():
    sig = Signal(**_signal())
    assert sig.id == "SIG-1"
    assert sig.cycle_s == 120.0
    assert len(sig.phases) == 4


def test_signal_zero_cycle_rejected():
    with pytest.raises(ValidationError):
        Signal(**{**_signal(), "cycle_s": 0})


def test_signal_negative_cycle_rejected():
    with pytest.raises(ValidationError):
        Signal(**{**_signal(), "cycle_s": -60.0})


def test_signal_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        Signal(**{**_signal(), "extra": "no"})


# =============================================================================
# Intersection
# =============================================================================

def test_intersection_valid():
    ix = Intersection(
        id="INT-1",
        name="Test Junction",
        lanes=[Lane(**_lane("N-L1", "N")), Lane(**_lane("S-L1", "S"))],
        paths=[Path(**_path())],
        signal=Signal(**_signal()),
    )
    assert ix.id == "INT-1"
    assert len(ix.lanes) == 2
    assert len(ix.paths) == 1
    assert ix.city == ""
    assert ix.control_type == ""
    assert ix.coord_system == ""
    assert ix.lat is None
    assert ix.lng is None


def test_intersection_with_metadata():
    ix = Intersection(
        id="INT-1",
        name="Test Junction",
        lanes=[Lane(**_lane("N-L1", "N"))],
        paths=[Path(**_path())],
        signal=Signal(**_signal()),
        city="Pune, Maharashtra",
        control_type="Pre-Timed Signal",
        coord_system="WGS 84",
        lat=18.5074,
        lng=73.8077,
    )
    assert ix.city == "Pune, Maharashtra"
    assert ix.control_type == "Pre-Timed Signal"
    assert ix.coord_system == "WGS 84"
    assert ix.lat == 18.5074
    assert ix.lng == 73.8077


def test_intersection_missing_name_rejected():
    with pytest.raises(ValidationError):
        Intersection(id="INT-1", lanes=[], paths=[], signal=Signal(**_signal()))


def test_intersection_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        Intersection(id="INT-1", name="X", lanes=[], paths=[],
                     signal=Signal(**_signal()), extra="bad")


# =============================================================================
# DemandRecord
# =============================================================================

def test_demand_record_valid():
    dr = DemandRecord(approach="N", movement="through",
                      vehicle_class="Passenger Car", vehicles_per_hour=450.0)
    assert dr.vehicles_per_hour == 450.0


def test_demand_record_zero_vph_allowed():
    dr = DemandRecord(approach="E", movement="left",
                      vehicle_class="Two-Wheeler", vehicles_per_hour=0.0)
    assert dr.vehicles_per_hour == 0.0


def test_demand_record_negative_vph_rejected():
    with pytest.raises(ValidationError):
        DemandRecord(approach="N", movement="through",
                     vehicle_class="Passenger Car", vehicles_per_hour=-10.0)


def test_demand_record_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        DemandRecord(approach="N", movement="through",
                     vehicle_class="Passenger Car", vehicles_per_hour=100.0,
                     extra="bad")


# =============================================================================
# TrajectoryPoint
# =============================================================================

def test_trajectory_point_valid():
    tp = TrajectoryPoint(t=0.0, s=0.0, speed_mps=10.0, accel_mps2=-1.5)
    assert tp.accel_mps2 == -1.5


def test_trajectory_point_zero_speed_allowed():
    tp = TrajectoryPoint(t=5.0, s=20.0, speed_mps=0.0, accel_mps2=0.0)
    assert tp.speed_mps == 0.0


def test_trajectory_point_negative_speed_rejected():
    with pytest.raises(ValidationError):
        TrajectoryPoint(t=1.0, s=5.0, speed_mps=-1.0, accel_mps2=0.0)


# =============================================================================
# Trajectory
# =============================================================================

def test_trajectory_valid():
    traj = Trajectory(
        vehicle_id="VEH-001",
        vehicle_class="Passenger Car",
        path_id="P-NS",
        points=[
            TrajectoryPoint(t=0.0, s=0.0, speed_mps=10.0, accel_mps2=0.0),
            TrajectoryPoint(t=0.1, s=1.0, speed_mps=10.0, accel_mps2=0.0),
        ],
    )
    assert traj.vehicle_id == "VEH-001"
    assert len(traj.points) == 2


def test_trajectory_missing_path_id_rejected():
    with pytest.raises(ValidationError):
        Trajectory(vehicle_id="VEH-001", vehicle_class="Passenger Car", points=[])


def test_trajectory_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        Trajectory(vehicle_id="V1", vehicle_class="Passenger Car",
                   path_id="P-NS", points=[], extra="bad")


# =============================================================================
# SafetyResult
# =============================================================================

def test_safety_result_feasible():
    sr = SafetyResult(intersection_id="INT-1", feasible=True, margin=2.5)
    assert sr.feasible is True
    assert sr.violations == []          # default


def test_safety_result_with_violations():
    sr = SafetyResult(intersection_id="INT-1", feasible=False, margin=-0.3,
                      violations=["N-left conflicts with E-through at t=12.4s"])
    assert not sr.feasible
    assert len(sr.violations) == 1


def test_safety_result_violations_default_empty():
    sr = SafetyResult(intersection_id="INT-1", feasible=True, margin=1.0)
    assert sr.violations == []


def test_safety_result_missing_margin_rejected():
    with pytest.raises(ValidationError):
        SafetyResult(intersection_id="INT-1", feasible=True)


def test_safety_result_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        SafetyResult(intersection_id="INT-1", feasible=True, margin=1.0, extra="bad")


# =============================================================================
# MacroSample
# =============================================================================

def test_macro_sample_valid():
    ms = MacroSample(timestamp_s=60.0, approach="N",
                     density_veh_per_km=25.0, speed_kmh=40.0, flow_veh_per_hr=1000.0)
    assert ms.flow_veh_per_hr == 1000.0


def test_macro_sample_all_zeros_allowed():
    ms = MacroSample(timestamp_s=0.0, approach="S",
                     density_veh_per_km=0.0, speed_kmh=0.0, flow_veh_per_hr=0.0)
    assert ms.density_veh_per_km == 0.0


def test_macro_sample_negative_density_rejected():
    with pytest.raises(ValidationError):
        MacroSample(timestamp_s=10.0, approach="N",
                    density_veh_per_km=-1.0, speed_kmh=40.0, flow_veh_per_hr=1000.0)


def test_macro_sample_negative_speed_rejected():
    with pytest.raises(ValidationError):
        MacroSample(timestamp_s=10.0, approach="N",
                    density_veh_per_km=20.0, speed_kmh=-5.0, flow_veh_per_hr=800.0)


def test_macro_sample_negative_flow_rejected():
    with pytest.raises(ValidationError):
        MacroSample(timestamp_s=10.0, approach="N",
                    density_veh_per_km=20.0, speed_kmh=40.0, flow_veh_per_hr=-100.0)


def test_macro_sample_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        MacroSample(timestamp_s=10.0, approach="N",
                    density_veh_per_km=20.0, speed_kmh=40.0,
                    flow_veh_per_hr=800.0, extra="bad")

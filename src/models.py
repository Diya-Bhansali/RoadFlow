from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Vehicle  (original model — preserved exactly from commit 268310a)
# ---------------------------------------------------------------------------

class Vehicle(BaseModel):
    """
    Pydantic model representing a vehicle's parameters.

    This model serves as the data contract for vehicle properties used in the
    microscopic traffic simulation physics engine (IDM + MOBIL).
    """
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid"
    )

    vehicle_class: str = Field(
        ...,
        alias="class",
        description="The type/class of the vehicle (e.g., 'Passenger Car', 'Two-Wheeler', 'Auto-rickshaw').",
    )
    length: float = Field(
        ...,
        gt=0,
        description="Length of the vehicle in meters (must be positive).",
    )
    max_accel: float = Field(
        ...,
        gt=0,
        description="Maximum acceleration limit in m/s^2 (must be positive).",
    )
    max_decel: float = Field(
        ...,
        gt=0,
        description="Maximum deceleration limit in m/s^2 (must be positive).",
    )
    desired_speed: float = Field(
        ...,
        gt=0,
        description="Desired free-flow speed of the vehicle in m/s (must be positive).",
    )


# ---------------------------------------------------------------------------
# Lane
# ---------------------------------------------------------------------------

class Lane(BaseModel):
    """A single lane on one approach arm of an intersection."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique lane identifier, e.g. 'N-L1'.")
    approach: Literal["N", "S", "E", "W"] = Field(
        ..., description="Cardinal direction of the approach this lane belongs to."
    )
    width_m: float = Field(
        ..., gt=0, description="Lane width in metres (must be > 0)."
    )
    allowed_movements: list[str] = Field(
        ...,
        description="Permitted movements from this lane, e.g. ['through', 'left', 'right'].",
    )
    vehicle_classes: list[str] = Field(
        ...,
        description="Vehicle classes permitted in this lane, e.g. ['Passenger Car', 'Two-Wheeler'].",
    )


# ---------------------------------------------------------------------------
# Path  (with nested PathPoint)
# ---------------------------------------------------------------------------

class PathPoint(BaseModel):
    """A single geometry point along a vehicle path through the intersection box."""

    model_config = ConfigDict(extra="forbid")

    s: float = Field(..., description="Distance along the path in metres.")
    x: float = Field(..., description="World X coordinate in metres.")
    y: float = Field(..., description="World Y coordinate in metres.")
    curvature: float = Field(
        ...,
        description="Path curvature at this point (1/radius, signed, m^-1). Zero = straight.",
    )


class Path(BaseModel):
    """A conflict-free vehicle path connecting one entry lane to one exit lane."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique path identifier, e.g. 'N-L1_to_S-L1'.")
    entry_lane_id: str = Field(..., description="ID of the entry lane.")
    exit_lane_id: str = Field(..., description="ID of the exit lane.")
    movement: str = Field(
        ..., description="Movement type: 'through', 'left', or 'right'."
    )
    points: list[PathPoint] = Field(
        ..., description="Ordered list of path geometry points."
    )
    speed_limit_mps: float = Field(
        ..., gt=0, description="Speed limit along this path in m/s (must be > 0)."
    )


# ---------------------------------------------------------------------------
# Signal  (with nested SignalPhase)
# ---------------------------------------------------------------------------

class SignalPhase(BaseModel):
    """A single phase within a traffic signal cycle."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Phase identifier, e.g. 'P1'.")
    active_movement_ids: list[str] = Field(
        ..., description="Path IDs (movements) that have green during this phase."
    )
    duration_s: float = Field(
        ..., gt=0, description="Duration of this phase in seconds (must be > 0)."
    )


class Signal(BaseModel):
    """Traffic signal controller for one intersection."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique signal identifier.")
    cycle_s: float = Field(
        ..., gt=0, description="Total signal cycle length in seconds (must be > 0)."
    )
    phases: list[SignalPhase] = Field(
        ..., description="Ordered list of signal phases."
    )


# ---------------------------------------------------------------------------
# Intersection
# ---------------------------------------------------------------------------

class Intersection(BaseModel):
    """A single at-grade intersection with lanes, conflict paths, and a signal."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique intersection identifier.")
    name: str = Field(..., description="Human-readable name of the intersection.")
    lanes: list[Lane] = Field(..., description="All lanes across all approach arms.")
    paths: list[Path] = Field(
        ..., description="All vehicle paths through the intersection box."
    )
    signal: Signal = Field(..., description="Signal controller for this intersection.")


# ---------------------------------------------------------------------------
# DemandRecord
# ---------------------------------------------------------------------------

class DemandRecord(BaseModel):
    """One origin-approach OD demand row."""

    model_config = ConfigDict(extra="forbid")

    approach: str = Field(..., description="Origin approach: N, S, E, or W.")
    movement: str = Field(
        ..., description="Movement type: 'through', 'left', or 'right'."
    )
    vehicle_class: str = Field(
        ..., description="Vehicle class, e.g. 'Passenger Car'."
    )
    vehicles_per_hour: float = Field(
        ..., ge=0, description="Demand flow rate in vehicles per hour (must be >= 0)."
    )


# ---------------------------------------------------------------------------
# Trajectory  (with nested TrajectoryPoint)
# ---------------------------------------------------------------------------

class TrajectoryPoint(BaseModel):
    """Kinematic state of one vehicle at one simulation time step."""

    model_config = ConfigDict(extra="forbid")

    t: float = Field(..., description="Simulation time in seconds.")
    s: float = Field(..., description="Distance along the vehicle path in metres.")
    speed_mps: float = Field(
        ..., ge=0, description="Speed in m/s (must be >= 0)."
    )
    accel_mps2: float = Field(
        ...,
        description="Longitudinal acceleration in m/s^2 (negative = deceleration).",
    )


class Trajectory(BaseModel):
    """Full kinematic trajectory of one vehicle through the intersection."""

    model_config = ConfigDict(extra="forbid")

    vehicle_id: str = Field(..., description="Unique identifier for this vehicle instance.")
    vehicle_class: str = Field(..., description="Vehicle class, e.g. 'Passenger Car'.")
    path_id: str = Field(..., description="ID of the Path this vehicle follows.")
    points: list[TrajectoryPoint] = Field(
        ..., description="Ordered time-series of kinematic states."
    )


# ---------------------------------------------------------------------------
# SafetyResult
# ---------------------------------------------------------------------------

class SafetyResult(BaseModel):
    """Output of a safety feasibility check for one intersection configuration."""

    model_config = ConfigDict(extra="forbid")

    intersection_id: str = Field(..., description="ID of the evaluated intersection.")
    feasible: bool = Field(
        ..., description="True if the configuration passes all safety checks."
    )
    margin: float = Field(
        ...,
        description=(
            "Safety margin scalar (positive = safe headway surplus in seconds; "
            "negative = conflict detected)."
        ),
    )
    violations: list[str] = Field(
        default_factory=list,
        description="Human-readable descriptions of any safety violations found.",
    )


# ---------------------------------------------------------------------------
# MacroSample
# ---------------------------------------------------------------------------

class MacroSample(BaseModel):
    """One macroscopic traffic observation (density–speed–flow triple)."""

    model_config = ConfigDict(extra="forbid")

    timestamp_s: float = Field(
        ..., description="Simulation clock time of the observation in seconds."
    )
    approach: str = Field(
        ..., description="Approach this sample was recorded on (N, S, E, or W)."
    )
    density_veh_per_km: float = Field(
        ..., ge=0, description="Traffic density in vehicles per kilometre (must be >= 0)."
    )
    speed_kmh: float = Field(
        ..., ge=0, description="Space-mean speed in km/h (must be >= 0)."
    )
    flow_veh_per_hr: float = Field(
        ..., ge=0, description="Flow rate in vehicles per hour (must be >= 0)."
    )

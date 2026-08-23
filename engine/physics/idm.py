"""
Intelligent Driver Model (IDM) for microscopic longitudinal traffic physics.

Formula
-------
acceleration = a * (1 - (v / v0)^delta - (s_star / s)^2)
where:
    s_star = s0 + max(0.0, v * T + (v * delta_v) / (2 * sqrt(a * b)))

Parameters
----------
v        : float - current speed (m/s)
v0       : float - desired speed (m/s)
s        : float | None - actual net gap to vehicle ahead (m). If None, no vehicle ahead.
delta_v  : float - closing speed = (own speed - lead speed) (m/s)
a        : float - maximum acceleration (m/s^2)
b        : float - comfortable deceleration (m/s^2)
s0       : float - minimum standstill gap (m)
T        : float - desired time headway (s)
delta    : float - acceleration exponent (standard = 4)
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class IDMParams:
    """Starting IDM physics parameters for a vehicle class."""

    desired_speed: float  # v0 in m/s
    max_accel: float  # a in m/s^2
    comfort_decel: float  # b in m/s^2
    min_gap: float  # s0 in meters
    time_headway: float  # T in seconds
    length: float  # vehicle length in meters
    delta: float = 4.0  # acceleration exponent


DEFAULT_IDM_PARAMS: dict[str, IDMParams] = {
    "Passenger Car": IDMParams(
        desired_speed=13.9,
        max_accel=1.0,
        comfort_decel=1.5,
        min_gap=2.0,
        time_headway=1.5,
        length=4.5,
    ),
    "Two-Wheeler": IDMParams(
        desired_speed=12.0,
        max_accel=1.8,
        comfort_decel=2.0,
        min_gap=1.0,
        time_headway=1.0,
        length=2.0,
    ),
    "Auto-Rickshaw": IDMParams(
        desired_speed=10.0,
        max_accel=0.8,
        comfort_decel=1.3,
        min_gap=1.5,
        time_headway=1.5,
        length=3.0,
    ),
}


def get_idm_params(vehicle_class: str) -> IDMParams:
    """
    Retrieve default IDM parameters for a vehicle class, case-insensitively
    supporting common name variants.
    """
    if vehicle_class in DEFAULT_IDM_PARAMS:
        return DEFAULT_IDM_PARAMS[vehicle_class]

    normalized = vehicle_class.lower().replace("-", " ").replace("_", " ").strip()
    for name, params in DEFAULT_IDM_PARAMS.items():
        norm_name = name.lower().replace("-", " ").replace("_", " ").strip()
        if normalized == norm_name:
            return params

    # Fallback to Passenger Car if unknown
    return DEFAULT_IDM_PARAMS["Passenger Car"]


def compute_idm_accel(
    v: float,
    v0: float,
    s: float | None = None,
    delta_v: float = 0.0,
    a: float = 1.0,
    b: float = 1.5,
    s0: float = 2.0,
    T: float = 1.5,
    delta: float = 4.0,
    max_decel_limit: float = 20.0,
) -> float:
    """
    Compute IDM longitudinal acceleration in m/s^2.

    Parameters:
    -----------
    v : float
        Current speed in m/s (>= 0).
    v0 : float
        Desired speed in m/s (> 0).
    s : float | None
        Actual gap to the lead vehicle (or stop line) in meters.
        If None, free-flow acceleration is returned.
    delta_v : float
        Closing speed (v - v_lead) in m/s. Positive when catching up.
    a : float
        Maximum acceleration in m/s^2.
    b : float
        Comfortable deceleration in m/s^2.
    s0 : float
        Minimum standstill distance in meters.
    T : float
        Desired time headway in seconds.
    delta : float
        Acceleration exponent (standard = 4.0).
    max_decel_limit : float
        Maximum hard braking limit in m/s^2 to prevent numeric infinities on overlap.

    Returns:
    --------
    float: Acceleration in m/s^2 (positive for acceleration, negative for braking).
    """
    v = max(0.0, v)
    if v0 <= 0.0:
        return -b

    # Free-road acceleration component
    free_flow_term = (v / v0) ** delta
    accel_free = a * (1.0 - free_flow_term)

    # If no obstacle/leader within sensing range, return free-flow acceleration
    if s is None:
        return accel_free

    # If gap is non-positive or extremely small, apply maximum braking
    if s <= 0.001:
        return -max_decel_limit

    # Interaction term s_star
    denom = 2.0 * math.sqrt(max(0.0001, a * b))
    dynamic_term = (v * delta_v) / denom
    s_star = s0 + max(0.0, v * T + dynamic_term)

    interaction_term = (s_star / s) ** 2
    accel = a * (1.0 - free_flow_term - interaction_term)

    # Numerical bound on emergency deceleration
    return max(-max_decel_limit, min(a, accel))

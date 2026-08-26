"""Physics sub-package for microscopic traffic models.

Implements IDM (Intelligent Driver Model) for longitudinal car-following
and MOBIL (Minimizing Overall Braking Induced by Lane Changes) for
lane change decision making.
"""

from engine.physics.idm import DEFAULT_IDM_PARAMS, IDMParams, compute_idm_accel, get_idm_params
from engine.physics.mobil import (
    check_mobil_incentive,
    check_mobil_safety,
    evaluate_mobil_lane_change,
    needs_lane_change,
)

__all__ = [
    "IDMParams",
    "DEFAULT_IDM_PARAMS",
    "compute_idm_accel",
    "get_idm_params",
    "needs_lane_change",
    "check_mobil_safety",
    "check_mobil_incentive",
    "evaluate_mobil_lane_change",
]

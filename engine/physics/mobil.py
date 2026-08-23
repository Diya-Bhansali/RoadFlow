"""
MOBIL (Minimizing Overall Braking Induced by Lane Changes) model.

Scope
-----
Implements a movement-directed MOBIL lane change evaluation:
1. Intent: A vehicle only evaluates changing lanes if its current lane does not
   allow its intended movement (e.g. vehicle in through-only lane needs to turn left).
2. Safety Criterion: The prospective follower in the target lane must not be forced
   to brake harder than safe deceleration limit b_safe (4.0 m/s^2).
3. Incentive Criterion: Total system acceleration gain must exceed threshold a_th (0.2 m/s^2)
   weighted by politeness factor p (0.3).
"""

from __future__ import annotations


def needs_lane_change(
    current_allowed_movements: list[str], intended_movement: str
) -> bool:
    """
    Check if a vehicle needs to change lanes to execute its intended movement.
    """
    return intended_movement not in current_allowed_movements


def check_mobil_safety(
    accel_new_follower_target: float,
    b_safe: float = 4.0,
) -> bool:
    """
    Evaluate MOBIL safety criterion:
    The new follower's prospective acceleration in the target lane must not fall
    below -b_safe (must not brake harder than b_safe).

    Parameters:
    -----------
    accel_new_follower_target : float
        Projected acceleration of the target lane's follower if lane change occurs (m/s^2).
    b_safe : float
        Maximum safe braking deceleration (m/s^2, positive scalar, default 4.0).

    Returns:
    --------
    bool: True if safe, False if follower would be forced to brake dangerously.
    """
    return accel_new_follower_target >= -b_safe


def check_mobil_incentive(
    accel_self_current: float,
    accel_self_target: float,
    accel_new_follower_current: float,
    accel_new_follower_target: float,
    accel_old_follower_current: float = 0.0,
    accel_old_follower_target: float = 0.0,
    p: float = 0.3,
    a_th: float = 0.2,
) -> bool:
    """
    Evaluate MOBIL incentive criterion:
    (a_self_target - a_self_current) + p * ((a_new_target - a_new_curr) + (a_old_target - a_old_curr)) > a_th

    Parameters:
    -----------
    accel_self_current : float
        Subject vehicle's acceleration in current lane.
    accel_self_target : float
        Subject vehicle's prospective acceleration in target lane.
    accel_new_follower_current : float
        New follower's current acceleration in target lane.
    accel_new_follower_target : float
        New follower's prospective acceleration in target lane.
    accel_old_follower_current : float
        Old follower's current acceleration in current lane.
    accel_old_follower_target : float
        Old follower's prospective acceleration after subject departs.
    p : float
        Politeness factor (default 0.3).
    a_th : float
        Incentive threshold in m/s^2 (default 0.2).

    Returns:
    --------
    bool: True if net incentive satisfies the threshold.
    """
    delta_self = accel_self_target - accel_self_current
    delta_new_follower = accel_new_follower_target - accel_new_follower_current
    delta_old_follower = accel_old_follower_target - accel_old_follower_current

    total_incentive = delta_self + p * (delta_new_follower + delta_old_follower)
    return total_incentive > a_th


def evaluate_mobil_lane_change(
    current_allowed_movements: list[str],
    intended_movement: str,
    accel_self_current: float,
    accel_self_target: float,
    accel_new_follower_current: float,
    accel_new_follower_target: float,
    accel_old_follower_current: float = 0.0,
    accel_old_follower_target: float = 0.0,
    p: float = 0.3,
    b_safe: float = 4.0,
    a_th: float = 0.2,
) -> bool:
    """
    Full simplified MOBIL decision for routing/movement-directed lane changes.
    """
    # 1. Only evaluate if vehicle actually needs to change lanes to make movement
    if not needs_lane_change(current_allowed_movements, intended_movement):
        return False

    # 2. Safety check: target follower braking
    if not check_mobil_safety(accel_new_follower_target, b_safe=b_safe):
        return False

    # 3. Incentive check
    if not check_mobil_incentive(
        accel_self_current=accel_self_current,
        accel_self_target=accel_self_target,
        accel_new_follower_current=accel_new_follower_current,
        accel_new_follower_target=accel_new_follower_target,
        accel_old_follower_current=accel_old_follower_current,
        accel_old_follower_target=accel_old_follower_target,
        p=p,
        a_th=a_th,
    ):
        return False

    return True

"""
Unit tests for IDM car-following and MOBIL lane-change physics engines.
"""

import pytest

from engine.physics.idm import (
    DEFAULT_IDM_PARAMS,
    IDMParams,
    compute_idm_accel,
    get_idm_params,
)
from engine.physics.mobil import (
    check_mobil_incentive,
    check_mobil_safety,
    evaluate_mobil_lane_change,
    needs_lane_change,
)


# =============================================================================
# 1. IDM Parameter Lookup Tests
# =============================================================================


def test_idm_param_lookup_all_classes():
    car = get_idm_params("Passenger Car")
    assert car.desired_speed == 13.9
    assert car.max_accel == 1.0
    assert car.comfort_decel == 1.5
    assert car.min_gap == 2.0
    assert car.time_headway == 1.5
    assert car.length == 4.5

    tw = get_idm_params("Two-Wheeler")
    assert tw.desired_speed == 12.0
    assert tw.max_accel == 1.8
    assert tw.comfort_decel == 2.0
    assert tw.min_gap == 1.0
    assert tw.time_headway == 1.0
    assert tw.length == 2.0

    auto = get_idm_params("Auto-Rickshaw")
    assert auto.desired_speed == 10.0
    assert auto.max_accel == 0.8
    assert auto.comfort_decel == 1.3
    assert auto.min_gap == 1.5
    assert auto.time_headway == 1.5
    assert auto.length == 3.0


def test_idm_param_lookup_case_variants():
    assert get_idm_params("passenger car").desired_speed == 13.9
    assert get_idm_params("two-wheeler").max_accel == 1.8
    assert get_idm_params("Auto-rickshaw").length == 3.0


# =============================================================================
# 2. Single Vehicle Free-Flow Tests
# =============================================================================


def test_single_vehicle_free_flow_acceleration():
    """
    A vehicle from standstill with no obstruction accelerates toward desired speed
    and does not exceed it.
    """
    v0 = 13.9
    a = 1.0
    v = 0.0
    dt = 0.1
    speeds = [v]

    for _ in range(600):  # 60 simulated seconds
        accel = compute_idm_accel(v=v, v0=v0, s=None, a=a)
        assert accel >= -0.01  # Should not decelerate in free-flow when v <= v0
        v = max(0.0, v + accel * dt)
        speeds.append(v)

    # Reaches very close to desired speed (~13.9 m/s)
    assert abs(v - v0) < 0.1
    # Never exceeds desired speed
    assert max(speeds) <= v0 + 1e-4


def test_single_vehicle_overspeed_deceleration():
    """
    A vehicle exceeding desired speed naturally decelerates toward v0 in free flow.
    """
    v0 = 10.0
    v = 15.0
    accel = compute_idm_accel(v=v, v0=v0, s=None, a=1.0)
    assert accel < 0.0  # Must brake to reach v0


# =============================================================================
# 3. Car-Following Tests (Lead Vehicle Interaction)
# =============================================================================


def test_following_vehicle_stopped_leader_safe_gap():
    """
    A following vehicle approaching a stationary lead vehicle must decelerate
    and come to a complete stop maintaining a safe gap (>= s0) without collision.
    """
    v0 = 13.9
    a = 1.0
    b = 1.5
    s0 = 2.0
    T = 1.5
    dt = 0.1

    # Lead vehicle stopped at s_lead = 50.0m
    s_lead = 50.0
    v_lead = 0.0
    lead_length = 4.5

    # Follower starts at s=0.0m with speed 10.0 m/s
    s_fol = 0.0
    v_fol = 10.0

    gaps = []

    for _ in range(500):  # 50 seconds
        net_gap = s_lead - s_fol - lead_length
        gaps.append(net_gap)

        if net_gap <= 0:
            break

        delta_v = v_fol - v_lead
        accel = compute_idm_accel(v=v_fol, v0=v0, s=net_gap, delta_v=delta_v, a=a, b=b, s0=s0, T=T)
        v_fol = max(0.0, v_fol + accel * dt)
        s_fol += v_fol * dt

    # Final speed must be zero (stopped)
    assert v_fol < 0.05
    # The gap must never become negative
    assert min(gaps) > 0.0
    # The final equilibrium gap should be >= standstill distance s0
    final_gap = s_lead - s_fol - lead_length
    assert final_gap >= s0 * 0.95


def test_following_vehicle_slower_moving_leader():
    """
    A follower catching up to a slower moving leader adapts its speed to match the leader.
    """
    v0 = 13.9
    v_lead = 6.0
    v_fol = 12.0
    s_lead = 80.0
    s_fol = 0.0
    lead_len = 4.5
    dt = 0.1

    for _ in range(600):
        net_gap = s_lead - s_fol - lead_len
        assert net_gap > 0.0, "Gap must never be negative"

        delta_v = v_fol - v_lead
        accel = compute_idm_accel(
            v=v_fol, v0=v0, s=net_gap, delta_v=delta_v, a=1.0, b=1.5, s0=2.0, T=1.5
        )
        v_fol = max(0.0, v_fol + accel * dt)
        s_fol += v_fol * dt
        s_lead += v_lead * dt

    # Follower speed matches leader speed within small tolerance
    assert abs(v_fol - v_lead) < 0.2


# =============================================================================
# 4. MOBIL Lane-Change Tests
# =============================================================================


def test_mobil_needs_lane_change():
    # In through lane, wants through -> False
    assert not needs_lane_change(["through"], "through")
    # In through lane, wants left -> True
    assert needs_lane_change(["through"], "left")
    # In multi-movement lane [through, left], wants left -> False
    assert not needs_lane_change(["through", "left"], "left")


def test_mobil_safety_criterion():
    # New follower prospective deceleration is -2.0 m/s^2 (within b_safe = 4.0) -> Safe
    assert check_mobil_safety(-2.0, b_safe=4.0)
    # Exactly at boundary -4.0 m/s^2 -> Safe
    assert check_mobil_safety(-4.0, b_safe=4.0)
    # Exceeds safe deceleration at -4.5 m/s^2 -> Unsafe
    assert not check_mobil_safety(-4.5, b_safe=4.0)


def test_mobil_incentive_criterion():
    # Self gains +1.0 m/s^2, new follower loses -0.5 m/s^2, old follower gains +0.2 m/s^2
    # Net = 1.0 + 0.3 * (-0.5 + 0.2) = 1.0 - 0.09 = 0.91 > 0.2 -> True
    assert check_mobil_incentive(
        accel_self_current=-0.5,
        accel_self_target=0.5,
        accel_new_follower_current=0.0,
        accel_new_follower_target=-0.5,
        accel_old_follower_current=-0.2,
        accel_old_follower_target=0.0,
        p=0.3,
        a_th=0.2,
    )

    # No advantage: self gains +0.1, others 0 -> 0.1 <= 0.2 -> False
    assert not check_mobil_incentive(
        accel_self_current=0.0,
        accel_self_target=0.1,
        accel_new_follower_current=0.0,
        accel_new_follower_target=0.0,
        p=0.3,
        a_th=0.2,
    )


def test_evaluate_mobil_lane_change_full():
    # 1. No need to change -> returns False immediately
    res1 = evaluate_mobil_lane_change(
        current_allowed_movements=["through"],
        intended_movement="through",
        accel_self_current=0.0,
        accel_self_target=1.0,
        accel_new_follower_current=0.0,
        accel_new_follower_target=0.0,
    )
    assert not res1

    # 2. Needs change, safe and advantageous -> returns True
    res2 = evaluate_mobil_lane_change(
        current_allowed_movements=["through"],
        intended_movement="left",
        accel_self_current=-1.0,
        accel_self_target=0.5,
        accel_new_follower_current=0.0,
        accel_new_follower_target=-1.0,
    )
    assert res2

    # 3. Needs change, but causes dangerous follower braking (-5.0 m/s^2) -> returns False
    res3 = evaluate_mobil_lane_change(
        current_allowed_movements=["through"],
        intended_movement="left",
        accel_self_current=-1.0,
        accel_self_target=1.0,
        accel_new_follower_current=0.0,
        accel_new_follower_target=-5.0,
    )
    assert not res3

import pytest
from pydantic import ValidationError

from src.models import Vehicle


def test_vehicle_instantiation_by_alias():
    # Test valid vehicle creation using the "class" alias
    data = {
        "class": "Passenger Car",
        "length": 4.5,
        "max_accel": 2.5,
        "max_decel": 4.5,
        "desired_speed": 15.0
    }
    vehicle = Vehicle(**data)
    assert vehicle.vehicle_class == "Passenger Car"
    assert vehicle.length == 4.5
    assert vehicle.max_accel == 2.5
    assert vehicle.max_decel == 4.5
    assert vehicle.desired_speed == 15.0

def test_vehicle_instantiation_by_name():
    # Test valid vehicle creation using field names directly (populate_by_name)
    vehicle = Vehicle(
        vehicle_class="Two-Wheeler",
        length=1.8,
        max_accel=3.5,
        max_decel=5.0,
        desired_speed=12.0
    )
    assert vehicle.vehicle_class == "Two-Wheeler"
    assert vehicle.length == 1.8

def test_vehicle_validation_errors():
    # Test missing fields
    with pytest.raises(ValidationError):
        Vehicle(length=4.5)

    # Test invalid length (must be positive)
    with pytest.raises(ValidationError):
        Vehicle(
            vehicle_class="Auto-rickshaw",
            length=0,
            max_accel=1.5,
            max_decel=2.0,
            desired_speed=9.0
        )

    # Test invalid negative max_accel
    with pytest.raises(ValidationError):
        Vehicle(
            vehicle_class="Auto-rickshaw",
            length=2.5,
            max_accel=-1.0,
            max_decel=2.0,
            desired_speed=9.0
        )

def test_vehicle_extra_fields_forbidden():
    # Test that extra fields are forbidden
    data = {
        "class": "Passenger Car",
        "length": 4.5,
        "max_accel": 2.5,
        "max_decel": 4.5,
        "desired_speed": 15.0,
        "extra_field": "not_allowed"
    }
    with pytest.raises(ValidationError):
        Vehicle(**data)

def test_vehicle_serialization():
    vehicle = Vehicle(
        vehicle_class="Passenger Car",
        length=4.5,
        max_accel=2.5,
        max_decel=4.5,
        desired_speed=15.0
    )
    
    # Check serialization to dict with aliases
    serialized = vehicle.model_dump(by_alias=True)
    assert "class" in serialized
    assert serialized["class"] == "Passenger Car"
    assert serialized["length"] == 4.5

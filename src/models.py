from pydantic import BaseModel, ConfigDict, Field


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
        description="The type/class of the vehicle (e.g., 'Passenger Car', 'Two-Wheeler', 'Auto-rickshaw')."
    )
    length: float = Field(
        ...,
        gt=0,
        description="Length of the vehicle in meters (must be positive)."
    )
    max_accel: float = Field(
        ...,
        gt=0,
        description="Maximum acceleration limit in m/s^2 (must be positive)."
    )
    max_decel: float = Field(
        ...,
        gt=0,
        description="Maximum deceleration limit in m/s^2 (must be positive)."
    )
    desired_speed: float = Field(
        ...,
        gt=0,
        description="Desired free-flow speed of the vehicle in m/s (must be positive)."
    )

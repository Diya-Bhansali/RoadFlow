"""Simulation sub-package for discrete-time microscopic traffic simulation.

Provides the main simulation loop and vehicle state management for
intersection traffic analysis.
"""

from engine.simulation.loop import SimVehicle, run_simulation

__all__ = ["SimVehicle", "run_simulation"]

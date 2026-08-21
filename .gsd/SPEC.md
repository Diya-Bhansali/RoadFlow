# SPEC.md — Project Specification

> **Status**: `FINALIZED`

## Vision
RoadFlow is a digital-twin platform for road and intersection design that closes the loop from traffic simulation to evaluation and optimization. Planners can load pre-configured intersection templates, tune parameters like lanes, curvature, and signal timings, simulate mixed Indian traffic using custom microscopic physics (IDM + MOBIL), and run an optimization engine to recommend the safest and most efficient design configuration before physical construction.

## Goals
1. **Heterogeneous Traffic Micro-Simulation**: Build a custom Python micro-simulation engine (dt = 0.1s) utilizing the Intelligent Driver Model (IDM) and MOBIL lane-changing model parameterized for distinct Indian vehicle classes (Passenger Cars, Two-Wheelers, Auto-rickshaws).
2. **Grid-Search Design Optimizer**: Implement a swappable design optimizer that sweeps through combinations of discrete parameters (lane counts, signal-timing splits, curve radii) and ranks them using safety limits, travel time, and queue length metrics.
3. **Pydantic Data Contract & API**: Define robust Pydantic data models for the entire traffic domain and expose them via a FastAPI backend to serve as a single source of truth for the engine, simulation, and frontend.
4. **Interactive Planner Dashboard**: Create a React + TS frontend dashboard with a Leaflet map for site context, custom interactive SVG design canvas templates showing the parameterized intersection layout, and trajectory playback visualizations.

## Non-Goals (Out of Scope)
- Multi-intersection networks, corridor-level corridors, or city-scale traffic planning.
- Pedestrian, bicycle, or animal traffic simulation.
- Real-time traffic sensor integration or live/streaming demand data.
- Freeform CAD-style drawing of arbitrary intersection geometry.
- Sophisticated evolutionary optimization algorithms (e.g., Genetic Algorithms, Bayesian Optimization) for the MVP.
- Hard runtime dependencies on SUMO and TraCI for the simulation flow (SUMO is for offline cross-validation only).

## Users
- **Urban & Traffic Planners**: Who need to test design ideas and signal plans against local traffic demands without expensive software licenses or manual redesigns.
- **Hackathon Judges**: Who need a clear, explainable visual demo demonstrating how changing road geometry and signal parameters directly improves throughput and safety.

## Constraints
- **Simulation Time step**: Fixed at `dt = 0.1` seconds.
- **Mixed Traffic**: Limited to Passenger Cars, Two-Wheelers, and Auto-rickshaws with parameterized IDM/MOBIL physics constraints.
- **Database**: PostgreSQL + PostGIS.
- **Frontend/Backend contract**: Strictly mediated by Pydantic models served directly as JSON via FastAPI.

## Success Criteria
- [ ] Pydantic models cover all key domain entities (`Intersection`, `Lane`, `Path`, `Signal`, `Vehicle`, `Trajectory`, `SafetyResult`, `DemandRecord`, `MacroSample`).
- [ ] Physics simulation runs custom IDM + MOBIL equations and updates coordinates correctly for all vehicle classes.
- [ ] Optimization grid-search returns the best configuration from a parameter space within a reasonable timeframe (< 10 seconds).
- [ ] React frontend renders the intersection geometry as interactive SVG using template controls and displays vehicle trajectory playbacks.

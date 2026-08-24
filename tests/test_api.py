"""
Pytest tests for ``api.main``.

Coverage
--------
- ``test_get_canonical_scenario``: GET /scenarios/canonical_4arm returns 200 and valid data.
- ``test_get_intersection``: GET /intersections/{id} returns 200 and valid Intersection.
- ``test_simulate_intersection``: POST /intersections/{id}/simulate returns 200 and valid trajectories and macro samples.
- ``test_get_safety_evaluation``: GET /intersections/{id}/safety returns 200 and valid SafetyResult.
- ``test_get_full_evaluation``: GET /intersections/{id}/evaluation returns 200 and valid EvaluationResponse.
"""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_get_canonical_scenario():
    response = client.get("/scenarios/canonical_4arm")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "INT-CANONICAL-4ARM"
    assert "lanes" in data
    assert "paths" in data
    assert "signal" in data
    assert len(data["lanes"]) == 12
    assert len(data["paths"]) == 12


def test_get_intersection():
    response = client.get("/intersections/INT-CANONICAL-4ARM")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "INT-CANONICAL-4ARM"
    assert data["name"] == "Canonical 4-Arm Signalised Intersection"


def test_simulate_intersection():
    response = client.post("/intersections/INT-CANONICAL-4ARM/simulate")
    assert response.status_code == 200
    data = response.json()
    assert "trajectories" in data
    assert "macro_samples" in data
    assert len(data["trajectories"]) > 0


def test_get_safety_evaluation():
    response = client.get("/intersections/INT-CANONICAL-4ARM/safety")
    assert response.status_code == 200
    data = response.json()
    assert data["intersection_id"] == "INT-CANONICAL-4ARM"
    assert "feasible" in data
    assert "margin" in data
    assert "violations" in data


def test_get_full_evaluation():
    response = client.get("/intersections/INT-CANONICAL-4ARM/evaluation")
    assert response.status_code == 200
    data = response.json()
    assert data["intersection_id"] == "INT-CANONICAL-4ARM"
    assert "cost" in data
    assert data["cost"] > 0
    assert "avg_travel_time" in data
    assert "avg_queue_length" in data
    assert "combined_score" in data

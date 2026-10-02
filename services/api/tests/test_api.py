"""Happy-path API test: plants -> scenario -> run -> results -> compare."""
import pytest
from fastapi.testclient import TestClient

from app.devdata import main as load_devdata
from app.main import app
from app.operator_auth import require_operator


@pytest.fixture
def client():
    load_devdata()
    app.dependency_overrides[require_operator] = lambda: "operator@example.com"
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def test_full_happy_path(client):
    with client:
        # explicit synthetic fixture
        plants = client.get("/api/v1/plants").json()
        assert len(plants) == 1
        assert plants[0]["code"] == "DEMO001"
        plant_id = plants[0]["id"]

        detail = client.get(f"/api/v1/plants/{plant_id}").json()
        assert detail["units"] and detail["compliance_limits"]

        # baseline scenario seeded
        scenarios = client.get(f"/api/v1/plants/{plant_id}/scenarios").json()
        assert any(s["is_baseline"] for s in scenarios)
        baseline_id = scenarios[0]["id"]

        # create a maintenance scenario
        resp = client.post(
            f"/api/v1/plants/{plant_id}/scenarios",
            json={
                "name": "High Demand + Planned Maintenance",
                "horizon": "3_months",
                "forecast": {"demand": "high", "weather": "wet"},
                "maintenance": [
                    {
                        "unit_type": "aeration",
                        "start_date": "2026-07-01",
                        "duration_days": 14,
                        "availability_pct": 50,
                    }
                ],
            },
        )
        assert resp.status_code == 201
        scenario_id = resp.json()["id"]

        # run both
        base_run = client.post(f"/api/v1/scenarios/{baseline_id}/run", json={}).json()
        scen_run = client.post(f"/api/v1/scenarios/{scenario_id}/run", json={}).json()
        assert base_run["status"] == "completed"
        assert base_run["validation_status"] == "illustrative_unvalidated"
        assert base_run["decision_use_permitted"] is False
        assert "compliance_pct" in scen_run["kpis"]

        # results
        ts = client.get(f"/api/v1/runs/{scen_run['id']}/timeseries").json()
        assert len(ts["dates"]) == 90
        assert "ammonia" in ts["series"]
        assert "ammonia" not in ts["compliance_limits"]

        # maintenance under higher demand should not outperform baseline
        assert scen_run["kpis"]["compliance_pct"] <= base_run["kpis"]["compliance_pct"]
        # GHG KPIs present and process-specific (SBR EFs synced from supabase)
        assert scen_run["kpis"]["ghg_mean_kgco2e_m3"] > 0
        assert "ch4_mean_kgco2e_m3" in scen_run["kpis"]

        # compare
        cmp = client.post("/api/v1/compare", json={"run_ids": [base_run["id"], scen_run["id"]]}).json()
        assert len(cmp["runs"]) == 2 and len(cmp["timeseries"]) == 2

        # models endpoint
        models = client.get("/api/v1/models").json()
        assert models[0]["model_id"] == "effluent_v1"


def test_validation_errors(client):
    with client:
        assert client.get("/api/v1/plants/9999").status_code == 404
        assert client.post("/api/v1/scenarios/9999/run", json={}).status_code == 404
        resp = client.post("/api/v1/compare", json={"run_ids": [99991, 99992]})
        assert resp.status_code == 404

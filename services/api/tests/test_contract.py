from fastapi.testclient import TestClient

from app.db.models import Scenario
from app.db.session import SessionLocal
from app.devdata import main as load_devdata
from app.main import app
from app.operator_auth import require_operator


def test_openapi_declares_versioned_routes_and_security():
    schema = app.openapi()
    assert schema["info"]["version"] == "1.0.0"
    assert "/api/v1/plants" in schema["paths"]
    assert "/api/v1/scenarios/{scenario_id}/run" in schema["paths"]
    assert "/api/v1/models" in schema["paths"]
    assert "HTTPBearer" in schema["components"]["securitySchemes"]
    run_properties = schema["components"]["schemas"]["RunOut"]["properties"]
    assert {"validation_status", "decision_use_permitted"} <= run_properties.keys()
    operation = schema["paths"]["/api/v1/plants/{plant_id}/scenarios"]["post"]
    assert {"401", "404", "422"} <= operation["responses"].keys()
    assert schema["components"]["schemas"]["ScenarioIn"]["examples"]
    assert schema["components"]["schemas"]["RunOut"]["examples"]


def test_missing_plant_has_stable_error_and_server_request_id():
    with TestClient(app) as client:
        response = client.get("/api/v1/plants/999999", headers={"X-Request-ID": "client-value"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "plant_not_found"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]
    assert response.headers["X-Request-ID"] != "client-value"


def test_invalid_scenario_has_field_details():
    load_devdata()
    app.dependency_overrides[require_operator] = lambda: "test-operator"
    try:
        with TestClient(app) as client:
            plant_id = client.get("/api/v1/plants").json()[0]["id"]
            response = client.post(
                f"/api/v1/plants/{plant_id}/scenarios",
                json={"name": "bad", "horizon": "three years"},
            )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "validation_error"
        assert response.json()["error"]["details"]
    finally:
        app.dependency_overrides.clear()


def test_missing_operator_cannot_create_scenario():
    load_devdata()
    with SessionLocal() as db:
        before = db.query(Scenario).count()
    with TestClient(app) as client:
        plant_id = client.get("/api/v1/plants").json()[0]["id"]
        response = client.post(
            f"/api/v1/plants/{plant_id}/scenarios", json={"name": "unauthorized"}
        )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"
    with SessionLocal() as db:
        assert db.query(Scenario).count() == before


def test_missing_scenario_and_run_have_specific_codes():
    app.dependency_overrides[require_operator] = lambda: "test-operator"
    try:
        with TestClient(app) as client:
            scenario = client.get("/api/v1/scenarios/999999")
            run = client.get("/api/v1/runs/999999")
        assert scenario.json()["error"]["code"] == "scenario_not_found"
        assert run.json()["error"]["code"] == "run_not_found"
    finally:
        app.dependency_overrides.clear()


def test_framework_route_errors_use_common_envelope():
    with TestClient(app) as client:
        missing = client.get("/api/v1/unknown")
        wrong_method = client.post("/api/v1/health")
    for response, code, status in (
        (missing, "not_found", 404),
        (wrong_method, "method_not_allowed", 405),
    ):
        assert response.status_code == status
        assert response.json()["error"]["code"] == code
        assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]

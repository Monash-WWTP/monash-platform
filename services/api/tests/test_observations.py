from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.identity.dependencies import require_account
from test_reporting import account

client = TestClient(app)


def body(observation=None):
    return {
        "protocol_id": "citizen-observation",
        "protocol_revision": 1,
        "observation": observation
        or {
            "kind": "flooding",
            "method": "visual",
            "response": "unknown",
            "surfaces": [],
        },
        "latitude": 3.123456,
        "longitude": 101.123456,
        "location_source": "selected",
        "observed_at": "2026-10-01T12:00:00Z",
        "note": "private context",
    }


def test_protocol_discovery_and_context_validation():
    r = client.get("/api/v2/observation-protocols")
    assert r.status_code == 200
    assert r.json()["protocol_revision"] == 1
    a = account(["report:own"])
    app.dependency_overrides[require_account] = lambda: a
    try:
        bad = [
            {
                "kind": "rainfall_accumulation",
                "method": "instrument",
                "value": 3,
                "unit": "mm",
            },
            {
                "kind": "water_reading",
                "method": "instrument",
                "value": -1,
                "unit": "m",
                "reference_kind": "depth",
                "reference_description": "road surface",
            },
            {"kind": "temperature", "method": "instrument", "value": 30, "unit": "°C"},
            {
                "kind": "water_appearance",
                "method": "visual",
                "response": "features_observed",
                "features": [],
            },
            {"kind": "rain_occurrence", "method": "visual", "response": "normal"},
        ]
        for obs in bad:
            assert (
                client.post(
                    "/api/v2/observations",
                    json=body(obs),
                    headers={"Idempotency-Key": str(uuid4())},
                ).status_code
                == 422
            )
    finally:
        app.dependency_overrides.clear()


def test_v2_ownership_retry_projection_and_v1_isolation():
    a = account(["report:own"])
    other = account(["report:own"])
    reviewer = account(["report:review"])
    app.dependency_overrides[require_account] = lambda: a
    try:
        payload = body()
        key = {"Idempotency-Key": str(uuid4())}
        r = client.post("/api/v2/observations", json=payload, headers=key)
        assert r.status_code == 201, r.text
        rid = r.json()["id"]
        assert (
            client.post("/api/v2/observations", json=payload, headers=key).json()["id"]
            == rid
        )
        assert (
            client.post(
                "/api/v2/observations", json={**payload, "note": "edited"}, headers=key
            ).status_code
            == 409
        )
        assert rid in [
            x["id"] for x in client.get("/api/v2/observations").json()["items"]
        ]
        assert rid not in [
            x["id"] for x in client.get("/api/v1/reports").json()["items"]
        ]
        assert client.get("/api/v1/reports/" + rid).status_code == 404
        app.dependency_overrides[require_account] = lambda: other
        assert client.get("/api/v2/observations/" + rid).status_code == 404
        app.dependency_overrides[require_account] = lambda: reviewer
        assert (
            client.post(
                "/api/v2/observations/" + rid + "/moderation",
                json={"status": "approved", "reason": "publication review"},
            ).status_code
            == 200
        )
        public = next(
            x
            for x in client.get("/api/v2/community/observations").json()["items"]
            if x["id"] == rid
        )
        assert public["latitude"] == 3.123
        assert (
            not {"note", "media_id", "owner_id", "location_accuracy_m", "review_reason"}
            & public.keys()
        )
        assert public["observation"]["response"] == "unknown"
        assert rid not in [
            x["id"]
            for x in client.get("/api/v1/community/observations").json()["items"]
        ]
    finally:
        app.dependency_overrides.clear()


def test_quantitative_contexts_and_legacy_retry_key_collision():
    a = account(["report:own"])
    app.dependency_overrides[require_account] = lambda: a
    try:
        rain = {
            "kind": "rainfall_accumulation",
            "method": "instrument",
            "value": 0,
            "unit": "mm",
            "amount_state": "value",
            "interval_start": "2026-10-01T10:00:00Z",
            "interval_end": "2026-10-01T12:00:00Z",
            "gauge_type": "manual gauge",
            "gauge_id": "test gauge",
        }
        for obs in [
            rain,
            {**rain, "amount_state": "trace", "value": None},
            {
                "kind": "temperature",
                "method": "instrument",
                "value": 20,
                "unit": "°C",
                "subject": "water",
                "instrument": "thermometer",
                "sample_context": "surface sample",
                "calibration_status": "unknown",
            },
        ]:
            r = client.post(
                "/api/v2/observations",
                json=body(obs),
                headers={"Idempotency-Key": str(uuid4())},
            )
            assert r.status_code == 201, r.text
        for obs in [
            {**rain, "interval_start": "2026-10-02T12:00:00Z"},
            {**rain, "amount_state": "trace"},
            {**rain, "interval_end": "2026-10-01T12:00:00"},
            {
                "kind": "water_reading",
                "method": "instrument",
                "value": -1,
                "unit": "m",
                "reference_kind": "stage",
                "reference_id": "unregistered",
                "reference_revision": 1,
            },
        ]:
            assert (
                client.post(
                    "/api/v2/observations",
                    json=body(obs),
                    headers={"Idempotency-Key": str(uuid4())},
                ).status_code
                == 422
            )
    finally:
        app.dependency_overrides.clear()


def test_registered_signed_stage_and_no_public_reference_identity():
    from app.db.platform import Station
    from app.db.session import SessionLocal

    reference = "qa-" + str(uuid4())
    with SessionLocal() as db:
        db.add(
            Station(
                code=reference,
                payload={
                    "code": reference,
                    "name": "QA reference",
                    "stp_type": None,
                    "category": None,
                    "latitude": 3.0,
                    "longitude": 101.0,
                    "created_at": "2026-10-01T12:00:00Z",
                    "stage_reference": {
                        "approved": True,
                        "revision": 1,
                        "unit": "m",
                        "label": "QA reference",
                    },
                },
            )
        )
        db.commit()
    a = account(["report:own"])
    app.dependency_overrides[require_account] = lambda: a
    try:
        obs = {
            "kind": "water_reading",
            "method": "instrument",
            "value": -0.2,
            "unit": "m",
            "reference_kind": "stage",
            "reference_id": reference,
            "reference_revision": 1,
            "instrument": "staff gauge",
        }
        r = client.post(
            "/api/v2/observations",
            json=body(obs),
            headers={"Idempotency-Key": str(uuid4())},
        )
        assert r.status_code == 201, r.text
        public_stations = client.get("/api/v1/monitoring/stations")
        assert public_stations.status_code == 200
        assert all("stage_reference" not in s for s in public_stations.json()["items"])
        assert client.get("/api/v2/observation-history?limit=200").status_code == 200
        page = client.get("/api/v2/observation-history").json()
        assert page["items"][0]["observation"]["value"] == -0.2
        assert any(
            x["id"] == reference
            for x in client.get("/api/v2/observation-references").json()["items"]
        )
    finally:
        app.dependency_overrides.clear()


def test_browser_callback_session_reaches_both_api_versions(monkeypatch):
    from datetime import timedelta
    import httpx
    from types import SimpleNamespace
    from app.routers import auth
    from app.db.platform import LoginAttempt, now
    from app.db.session import SessionLocal
    from app.identity.dependencies import digest

    a = account(["report:own"])
    state = str(uuid4())
    browser = str(uuid4())
    nonce = str(uuid4())
    with SessionLocal() as db:
        db.add(
            LoginAttempt(
                state_hash=digest(state),
                browser_hash=digest(browser),
                operator_login=True,
                verifier="test-verifier",
                nonce=nonce,
                expires_at=now() + timedelta(minutes=5),
            )
        )
        db.commit()
    monkeypatch.setattr(
        auth,
        "discovery",
        lambda: {
            "token_endpoint": "https://identity.invalid/token",
            "jwks_uri": "https://identity.invalid/keys",
        },
    )
    monkeypatch.setattr(
        auth.httpx,
        "post",
        lambda *a, **k: httpx.Response(
            200,
            json={"id_token": "test-token"},
            request=httpx.Request("POST", "https://identity.invalid/token"),
        ),
    )
    monkeypatch.setattr(
        auth,
        "signing_keys",
        lambda _: SimpleNamespace(
            get_signing_key_from_jwt=lambda _: SimpleNamespace(key="test-key")
        ),
    )
    monkeypatch.setattr(
        auth, "validate_token", lambda *a, **k: {"nonce": nonce, "amr": ["mfa"]}
    )
    monkeypatch.setattr(auth, "account_from_claims", lambda db, claims: a)
    browser_client = TestClient(app, base_url="https://testserver")
    browser_client.cookies.set("monash_login", browser)
    r = browser_client.get(
        "/api/v1/auth/callback",
        params={"code": "test-code", "state": state},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert browser_client.get("/api/v1/auth/me").status_code == 200
    assert browser_client.get("/api/v2/observation-history").status_code == 200


def test_revision_two_context_and_followup_privacy():
    a = account(["report:own"])
    other = account(["report:own"])
    app.dependency_overrides[require_account] = lambda: a

    def post(p):
        return client.post(
            "/api/v2/observations", json=p, headers={"Idempotency-Key": str(uuid4())}
        )

    try:
        assert client.get("/api/v2/observation-protocols").json().get(
            "supported_revisions"
        ) == [1, 2]
        original = {
            **body(
                {
                    "kind": "flooding",
                    "method": "visual",
                    "response": "present",
                    "surfaces": ["road"],
                    "movement": "flowing",
                }
            ),
            "protocol_revision": 2,
        }
        r = post(original)
        assert r.status_code == 201, r.text
        rid = r.json()["id"]
        update = {
            **original,
            "observed_at": "2026-10-01T13:00:00Z",
            "previous_observation_id": rid,
            "level_change": "higher",
        }
        r = post(update)
        assert r.status_code == 201, r.text
        assert r.json()["previous_observation_id"] == rid
        assert (
            post({**update, "observed_at": original["observed_at"]}).status_code == 422
        )
        assert post({**update, "latitude": 3.0}).status_code == 422
        assert post({**update, "location_accuracy_m": 5}).status_code == 422
        assert post({**original, "protocol_revision": 1}).status_code == 422
        assert post({**original, "level_change": "higher"}).status_code == 422
        assert post({**original, "photo_source": "camera"}).status_code == 422
        absent = {
            **update,
            "observation": {
                "kind": "flooding",
                "method": "visual",
                "response": "unknown",
                "surfaces": [],
            },
        }
        assert post(absent).status_code == 422
        assert (
            post({k: v for k, v in absent.items() if k != "level_change"}).status_code
            == 201
        )
        app.dependency_overrides[require_account] = lambda: other
        assert post(update).status_code == 404
        app.dependency_overrides[require_account] = lambda: account(["report:review"])
        assert (
            client.post(
                "/api/v2/observations/" + r.json()["id"] + "/moderation",
                json={"status": "approved", "reason": "QA"},
            ).status_code
            == 200
        )
        public = next(
            x
            for x in client.get("/api/v2/community/observations").json()["items"]
            if x["id"] == r.json()["id"]
        )
        assert public["protocol_revision"] == 2
        assert public["observation"]["movement"] == "flowing"
        assert (
            "previous_observation_id" not in public
            and "photo_source" not in public
            and "level_change" not in public
        )
    finally:
        app.dependency_overrides.clear()


def test_revision_two_photo_source_and_foreign_media():
    from app.db.platform import Media
    from app.db.session import SessionLocal

    a = account(["report:own"])
    other = account(["report:own"])
    mid = str(uuid4())
    with SessionLocal() as db:
        db.add(
            Media(
                id=mid,
                owner_id=a.id,
                object_key=str(uuid4()),
                sha256="0" * 64,
                byte_size=10,
                mime="image/png",
            )
        )
        db.commit()
    app.dependency_overrides[require_account] = lambda: a
    try:
        payload = {
            **body(),
            "protocol_revision": 2,
            "media_id": mid,
            "photo_source": "gallery",
        }
        r = client.post(
            "/api/v2/observations",
            json=payload,
            headers={"Idempotency-Key": str(uuid4())},
        )
        assert r.status_code == 201, r.text
        assert r.json()["photo_source"] == "gallery"
        assert (
            client.post(
                "/api/v2/observations",
                json={**payload, "photo_source": None},
                headers={"Idempotency-Key": str(uuid4())},
            ).status_code
            == 422
        )
        app.dependency_overrides[require_account] = lambda: other
        assert (
            client.post(
                "/api/v2/observations",
                json=payload,
                headers={"Idempotency-Key": str(uuid4())},
            ).status_code
            == 404
        )
    finally:
        app.dependency_overrides.clear()

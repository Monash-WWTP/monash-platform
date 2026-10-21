from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.identity.dependencies import require_account
from test_reporting import account
from test_observations import body

client = TestClient(app)


def test_response_permissions_and_atomic_lifecycle():
    citizen = account(["report:own"])
    responder = account(["report:respond"])
    app.dependency_overrides[require_account] = lambda: citizen
    try:
        r = client.post(
            "/api/v2/observations",
            json=body(),
            headers={"Idempotency-Key": str(uuid4())},
        )
        rid = r.json()["id"]
        url = "/api/v1/operations/reports/" + rid
        assert client.get(url).status_code == 403
        app.dependency_overrides[require_account] = lambda: responder
        responder._mfa_verified = False
        assert client.get(url).status_code == 403
        responder._mfa_verified = True
        assert client.get(url).json()["response"]["revision"] == 0

        def event(revision, action, **extra):
            return client.post(
                url + "/events",
                json={
                    "expected_revision": revision,
                    "action": action,
                    "reason": "QA synthetic test",
                    **extra,
                },
            )

        assert event(0, "close", note="No response required").status_code == 422
        r = event(0, "assign", assignee_id=responder.id)
        assert r.status_code == 200, r.text
        assert r.json()["response"]["state"] == "assigned"
        assert event(0, "acknowledge").status_code == 409
        assert event(1, "assign", assignee_id=citizen.id).status_code == 422
        assert (
            event(
                1,
                "inspect",
                result="confirmed",
                observed_at="2026-10-01T13:00:00Z",
                note="Visual inspection from public path",
            ).status_code
            == 200
        )
        assert event(2, "act", note="Checked drainage obstruction").status_code == 200
        r = event(3, "close", note="Inspection completed; referred to drainage team")
        assert r.status_code == 200, r.text
        assert r.json()["response"]["state"] == "closed"
        assert (
            event(4, "act", note="Cannot silently edit closed case").status_code == 409
        )
        r = event(4, "reopen")
        assert r.status_code == 200, r.text
        assert len(r.json()["events"]) == 5
        assert r.json()["report"]["moderation_status"] == "pending"
        assert r.json()["report"]["observation"]["response"] == "unknown"
        assert client.get("/api/v2/community/observations").status_code == 200
        responder.capabilities = []
        assert client.get(url).status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_response_browser_csrf_registry_and_audit():
    from datetime import timedelta
    from app.db.platform import (
        BrowserSession,
        AuditEvent,
        ReportResponseEvent,
        CitizenReport,
        Account,
        now,
    )
    from app.db.session import SessionLocal
    from app.identity.dependencies import digest
    from app.config import settings

    responder = account(["report:respond"])
    citizen = account(["report:own"])
    app.dependency_overrides[require_account] = lambda: citizen
    r = client.post(
        "/api/v1/reports",
        json={
            "category": "wastewater",
            "condition": "warning",
            "latitude": 3,
            "longitude": 101,
            "observed_at": "2026-10-01T12:00:00Z",
        },
        headers={"Idempotency-Key": str(uuid4())},
    )
    rid = r.json()["id"]
    app.dependency_overrides.clear()
    token, csrf = str(uuid4()), str(uuid4())
    with SessionLocal() as db:
        db.add(
            BrowserSession(
                token_hash=digest(token),
                account_id=responder.id,
                csrf_hash=digest(csrf),
                mfa_verified=True,
                expires_at=now() + timedelta(hours=1),
            )
        )
        db.commit()
    browser = TestClient(app)
    browser.cookies.set("monash_session", token)
    url = "/api/v1/operations/reports/" + rid
    payload = {
        "expected_revision": 0,
        "action": "acknowledge",
        "reason": "QA inspection",
    }
    assert browser.post(url + "/events", json=payload).status_code == 403
    headers = {"X-CSRF-Token": csrf, "Origin": settings.web_origin}
    assert (
        browser.post(
            url + "/events",
            json={**payload, "action": "associate", "plant_id": 99999999},
            headers=headers,
        ).status_code
        == 422
    )
    assert (
        browser.post(url + "/events", json=payload, headers=headers).status_code == 200
    )
    with SessionLocal() as db:
        assert db.query(ReportResponseEvent).filter_by(report_id=rid).count() == 1
        assert (
            db.query(AuditEvent)
            .filter_by(resource_id=rid, action="report.response.acknowledge")
            .count()
            == 1
        )
        assert db.get(CitizenReport, rid).status == "pending"
        a = db.get(Account, responder.id)
        a.capabilities = []
        db.commit()
    assert browser.get(url).status_code == 403


def test_trusted_cli_can_grant_responder():
    from app.identity.administration import set_capabilities
    from app.db.session import SessionLocal
    from app.db.platform import Account
    target=account(['report:own'])
    with SessionLocal() as db:
        set_capabilities(db,target.id,['report:own','report:respond'],'local QA','Approved synthetic operator test')
        assert 'report:respond' in db.get(Account,target.id).capabilities

from uuid import uuid4
from app.db.session import SessionLocal
from app.db.platform import CitizenReport
from app.migration.private import import_reports


def test_legacy_ownership_is_preserved_without_email_claims():
    identifier = str(uuid4())
    subject = str(uuid4())
    row = {
        "id": identifier,
        "reporter_id": subject,
        "category": "wastewater",
        "condition": "normal",
        "latitude": 3.06,
        "longitude": 101.62,
        "note": "private source note",
        "photo_path": None,
        "observed_at": "2025-01-01T00:00:00Z",
        "created_at": "2025-01-02T00:00:00Z",
        "moderation_status": "approved",
    }
    with SessionLocal() as db:
        first = import_reports(db, [row], source_id="isolated-test-" + identifier)
        assert first["reports"] == 1
        report = db.get(CitizenReport, identifier)
        assert report.owner_id is None and report.legacy_subject == subject
        assert report.payload["note"] == "private source note"
        assert report.status == "approved"
        assert (
            import_reports(db, [row], source_id="isolated-test-" + identifier) == first
        )


def test_photo_import_reconciles_bytes_and_custody(tmp_path, monkeypatch):
    import hashlib
    from io import BytesIO
    from PIL import Image
    from app.reporting import storage
    from app.db.platform import Media, Account
    from app.migration.private import import_private_bundle
    from test_media import MemoryStore

    store = MemoryStore()
    monkeypatch.setattr(storage, "client", lambda: store)
    identifier = str(uuid4())
    subject = str(uuid4())
    photo = BytesIO()
    Image.new("RGB", (8, 8), "white").save(photo, format="JPEG")
    root = tmp_path / "photos"
    root.mkdir()
    (root / "source.jpg").write_bytes(photo.getvalue())
    row = {
        "id": identifier,
        "reporter_id": subject,
        "category": "wastewater",
        "condition": "normal",
        "latitude": 3,
        "longitude": 101,
        "note": "private",
        "photo_path": "original/" + subject + "/source.jpg",
        "observed_at": "2025-01-01T00:00:00Z",
        "created_at": "2025-01-02T00:00:00Z",
        "moderation_status": "pending",
    }
    media = {
        row["photo_path"]: {
            "file": "source.jpg",
            "sha256": hashlib.sha256(photo.getvalue()).hexdigest(),
        }
    }
    with SessionLocal() as db:
        counts = import_private_bundle(
            db, [row], media, root, "photo-test-" + identifier
        )
        assert counts["photos"] == 1
        report = db.get(CitizenReport, identifier)
        assert report.owner_id is None
        item = db.get(Media, report.media_id)
        assert item.sha256 == media[row["photo_path"]]["sha256"]
        assert db.get(Account, item.owner_id).capabilities == []
        assert (
            import_private_bundle(db, [row], media, root, "photo-test-" + identifier)
            == counts
        )
    bad = {
        row["photo_path"]: {
            "file": "../outside.jpg",
            "sha256": media[row["photo_path"]]["sha256"],
        }
    }
    import pytest

    with SessionLocal() as db:
        with pytest.raises(ValueError):
            import_private_bundle(
                db, [{**row, "id": str(uuid4())}], bad, root, "bad-" + identifier
            )

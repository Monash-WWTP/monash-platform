"""Explicit private export import; anonymous subjects remain unclaimed until proof is presented."""

import hashlib, json
from datetime import datetime
from sqlalchemy.orm import Session
from ..db.platform import CitizenReport, ImportRecord, AuditEvent, Account, Media
from ..config import settings
from ..reporting.schemas import ReportInput


def import_reports(
    db: Session, rows: list[dict], source_id: str, commit: bool = True
) -> dict:
    digest = hashlib.sha256(
        json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    prior = db.get(ImportRecord, "private:" + source_id)
    if prior:
        if prior.digest != digest:
            raise ValueError("Private source changed under existing import identifier")
        return prior.manifest["reconciliation"]
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate legacy report identifiers")
    for raw in rows:
        if db.get(CitizenReport, raw["id"]):
            raise ValueError("Report identifier already exists")
        if raw.get("photo_path") and not raw.get("media_id"):
            raise ValueError(
                "Private photo must be reconciled into local storage before report import"
            )
        payload = {k: raw.get(k) for k in ReportInput.model_fields if k in raw}
        validated = ReportInput.model_validate(payload).model_dump(mode="json")
        status = raw.get("moderation_status")
        if status not in {"pending", "approved", "rejected"}:
            raise ValueError("Missing or invalid source moderation status")
        if validated.get("media_id"):
            media = db.get(Media, validated["media_id"])
            custodian = db.get(Account, media.owner_id) if media else None
            if (
                not custodian
                or custodian.issuer != "legacy:" + settings.supabase_url
                or custodian.subject != raw["reporter_id"]
            ):
                raise ValueError(
                    "Photo custody does not match the original report subject"
                )
        created = datetime.fromisoformat(raw["created_at"].replace("Z", "+00:00"))
        if created.tzinfo is None:
            raise ValueError("Source creation time requires timezone")
        db.add(
            CitizenReport(
                id=raw["id"],
                owner_id=None,
                legacy_subject=raw["reporter_id"],
                idempotency_key="legacy:" + raw["id"],
                payload_hash=hashlib.sha256(
                    json.dumps(validated, sort_keys=True).encode()
                ).hexdigest(),
                category=validated["category"],
                latitude=validated["latitude"],
                longitude=validated["longitude"],
                status=status,
                payload=validated,
                media_id=validated.get("media_id"),
                created_at=created,
            )
        )
        db.add(
            AuditEvent(
                actor_id=None,
                action="report.import",
                resource_id=raw["id"],
                details={
                    "source_id": source_id,
                    "source_status": status,
                    "reviewer_provenance": "unknown"
                    if not raw.get("reviewed_by")
                    else "source_recorded",
                    "source_reviewed_by": raw.get("reviewed_by"),
                    "source_reviewed_at": raw.get("reviewed_at"),
                },
            )
        )
    counts = {"reports": len(rows), "unclaimed": len(rows)}
    db.add(
        ImportRecord(
            source_id="private:" + source_id,
            digest=digest,
            manifest={"reconciliation": counts, "type": "private_legacy_reports"},
        )
    )
    if commit:
        db.commit()
    return counts


def import_private_bundle(
    db: Session, rows: list[dict], photos: dict, photo_root, source_id: str
) -> dict:
    """Validate every source photo before writing; rollback and remove newly written keys on failure."""
    from pathlib import Path
    from uuid import UUID, uuid4, uuid5, NAMESPACE_URL
    from io import BytesIO
    from PIL import Image
    from ..reporting import storage

    root = Path(photo_root).resolve()
    digest = hashlib.sha256(
        json.dumps({"rows": rows, "photos": photos}, sort_keys=True).encode()
    ).hexdigest()
    prior = db.get(ImportRecord, "bundle:" + source_id)
    if prior:
        if prior.digest != digest:
            raise ValueError("Bundle changed under existing import identifier")
        return prior.manifest["reconciliation"]
    prepared = {}
    owners = {}
    for row in rows:
        UUID(row["id"])
        UUID(row["reporter_id"])
        origin = row.get("photo_path")
        if not origin:
            continue
        mapping = photos.get(origin)
        if not mapping:
            raise ValueError("Source photo is missing from export manifest")
        path = (root / mapping["file"]).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("Photo path leaves authorized export directory")
        if path.stat().st_size > 10 * 1024 * 1024:
            raise ValueError("Source photo exceeds 10 MB")
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != mapping["sha256"]:
            raise ValueError("Source photo checksum mismatch")
        image = Image.open(BytesIO(content))
        if (
            image.format not in {"JPEG", "PNG", "WEBP"}
            or image.width * image.height > 25_000_000
        ):
            raise ValueError("Invalid source photo")
        mime = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}[
            image.format
        ]
        image.verify()
        if origin in owners and owners[origin] != row["reporter_id"]:
            raise ValueError(
                "Source photo is shared across different original subjects"
            )
        owners[origin] = row["reporter_id"]
        prepared[origin] = (content, mime, mapping["sha256"])
    created = []
    store = storage.client()
    mapped = {}
    try:
        for origin, (content, mime, sha) in prepared.items():
            subject = owners[origin]
            custodian = (
                db.query(Account)
                .filter_by(issuer="legacy:" + settings.supabase_url, subject=subject)
                .first()
            )
            if not custodian:
                custodian = Account(
                    issuer="legacy:" + settings.supabase_url,
                    subject=subject,
                    email="",
                    capabilities=[],
                )
                db.add(custodian)
                db.flush()
            media_id = str(uuid5(NAMESPACE_URL, source_id + ":" + origin))
            if db.get(Media, media_id):
                raise ValueError("Existing media requires a reconciled prior bundle")
            key = "legacy/" + subject + "/" + str(uuid4())
            store.put_object(
                Bucket=settings.storage_bucket, Key=key, Body=content, ContentType=mime
            )
            created.append(key)
            actual = store.get_object(Bucket=settings.storage_bucket, Key=key)[
                "Body"
            ].read(len(content) + 1)
            if hashlib.sha256(actual).hexdigest() != sha:
                raise ValueError("Stored source photo failed reconciliation")
            db.add(
                Media(
                    id=media_id,
                    owner_id=custodian.id,
                    object_key=key,
                    sha256=sha,
                    byte_size=len(content),
                    mime=mime,
                )
            )
            db.flush()
            mapped[origin] = media_id
        translated = [
            {
                **row,
                **(
                    {"media_id": mapped[row["photo_path"]]}
                    if row.get("photo_path")
                    else {}
                ),
            }
            for row in rows
        ]
        counts = {
            **import_reports(db, translated, source_id, commit=False),
            "photos": len(prepared),
        }
        db.add(
            ImportRecord(
                source_id="bundle:" + source_id,
                digest=digest,
                manifest={
                    "reconciliation": counts,
                    "type": "private_report_photo_bundle",
                },
            )
        )
        db.commit()
        return counts
    except Exception:
        db.rollback()
        for key in created:
            store.delete_object(Bucket=settings.storage_bucket, Key=key)
        raise

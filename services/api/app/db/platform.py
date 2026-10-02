"""Application-owned identity, monitoring, reporting and audit persistence."""
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import Boolean, String, DateTime, JSON, Float, ForeignKey, UniqueConstraint, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from .models import Base


def now():
    return datetime.now(timezone.utc)


def identifier():
    return str(uuid4())


class Account(Base):
    __tablename__ = 'accounts'
    __table_args__ = (UniqueConstraint('issuer','subject'),)
    id: Mapped[str] = mapped_column(String(36),primary_key=True,default=identifier)
    issuer: Mapped[str] = mapped_column(String,nullable=False)
    subject: Mapped[str] = mapped_column(String,nullable=False)
    email: Mapped[str] = mapped_column(String,nullable=False)
    capabilities: Mapped[list] = mapped_column(JSON,default=lambda:['report:own'])
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now)


class BrowserSession(Base):
    __tablename__ = 'browser_sessions'
    token_hash: Mapped[str] = mapped_column(String(64),primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey('accounts.id'),nullable=False)
    csrf_hash: Mapped[str] = mapped_column(String(64),nullable=False)
    mfa_verified: Mapped[bool] = mapped_column(Boolean,default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False)


class LoginAttempt(Base):
    __tablename__ = 'login_attempts'
    state_hash: Mapped[str] = mapped_column(String(64),primary_key=True)
    browser_hash: Mapped[str] = mapped_column(String(64),nullable=False)
    operator_login: Mapped[bool] = mapped_column(Boolean,default=False)
    verifier: Mapped[str] = mapped_column(String,nullable=False)
    nonce: Mapped[str] = mapped_column(String,nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False)


class Station(Base):
    __tablename__ = 'monitoring_stations'
    code: Mapped[str] = mapped_column(String,primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON,nullable=False)


class Sample(Base):
    __tablename__ = 'monitoring_samples'
    id: Mapped[int] = mapped_column(Integer,primary_key=True,autoincrement=False)
    station_code: Mapped[str] = mapped_column(ForeignKey('monitoring_stations.code'),index=True)
    payload: Mapped[dict] = mapped_column(JSON,nullable=False)


class ImportRecord(Base):
    __tablename__ = 'import_records'
    source_id: Mapped[str] = mapped_column(String,primary_key=True)
    digest: Mapped[str] = mapped_column(String(64),nullable=False)
    manifest: Mapped[dict] = mapped_column(JSON,nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now)


class Media(Base):
    __tablename__ = 'report_media'
    id: Mapped[str] = mapped_column(String(36),primary_key=True,default=identifier)
    owner_id: Mapped[str] = mapped_column(ForeignKey('accounts.id'),index=True)
    object_key: Mapped[str] = mapped_column(String,unique=True,nullable=False)
    sha256: Mapped[str] = mapped_column(String(64),nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer,nullable=False)
    mime: Mapped[str] = mapped_column(String,nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now)


class CitizenReport(Base):
    __tablename__ = 'citizen_reports'
    __table_args__ = (UniqueConstraint('owner_id','idempotency_key'),)
    id: Mapped[str] = mapped_column(String(36),primary_key=True,default=identifier)
    owner_id: Mapped[str | None] = mapped_column(ForeignKey('accounts.id'),index=True)
    legacy_subject: Mapped[str | None] = mapped_column(String)
    idempotency_key: Mapped[str] = mapped_column(String,nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64),nullable=False)
    category: Mapped[str] = mapped_column(String,nullable=False)
    latitude: Mapped[float] = mapped_column(Float,nullable=False)
    longitude: Mapped[float] = mapped_column(Float,nullable=False)
    status: Mapped[str] = mapped_column(String,default='pending',index=True)
    payload: Mapped[dict] = mapped_column(JSON,nullable=False)
    media_id: Mapped[str | None] = mapped_column(ForeignKey('report_media.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now)


class AuditEvent(Base):
    __tablename__ = 'audit_events'
    id: Mapped[str] = mapped_column(String(36),primary_key=True,default=identifier)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey('accounts.id'))
    action: Mapped[str] = mapped_column(String,nullable=False)
    resource_id: Mapped[str] = mapped_column(String,nullable=False)
    details: Mapped[dict] = mapped_column(JSON,nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now)

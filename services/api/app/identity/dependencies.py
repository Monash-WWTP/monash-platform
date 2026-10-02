"""Shared account resolution and server-owned capabilities."""
import hashlib
from datetime import datetime, timezone
from functools import lru_cache
import jwt
from fastapi import Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..config import settings
from ..db.session import get_db
from ..db.platform import Account, BrowserSession, now
from ..http.errors import ApiError
from .tokens import validate_token


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@lru_cache(maxsize=4)
def signing_keys(url: str):
    return jwt.PyJWKClient(url, timeout=5, lifespan=300)


def account_from_claims(db: Session, claims: dict) -> Account:
    account = db.query(Account).filter_by(issuer=claims['iss'],subject=claims['sub']).first()
    if account is None:
        account = Account(issuer=claims['iss'],subject=claims['sub'],email=claims.get('email',''))
        db.add(account)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            account = db.query(Account).filter_by(issuer=claims['iss'],subject=claims['sub']).one()
    return account


def authenticate_bearer(token: str) -> dict:
    if not settings.oidc_issuer or not settings.oidc_jwks_url:
        raise ApiError(503,'identity_unavailable','Identity is not configured')
    try:
        key = signing_keys(settings.oidc_jwks_url).get_signing_key_from_jwt(token).key
        return validate_token(token,key,settings.oidc_issuer,
                              [settings.oidc_client_id,settings.oidc_mobile_client_id,settings.oidc_operator_client_id])
    except (jwt.PyJWKClientConnectionError, OSError):
        raise ApiError(503,'identity_unavailable','Identity service is unavailable')
    except (ValueError,jwt.PyJWTError):
        raise ApiError(401,'invalid_session','Sign in with a verified account')


def require_account(request: Request, db: Session=Depends(get_db)) -> Account:
    authorization=request.headers.get('Authorization','')
    if authorization.startswith('Bearer '):
        claims=authenticate_bearer(authorization[7:])
        account=account_from_claims(db,claims)
        account._mfa_verified='mfa' in claims.get('amr',[])
        return account
    token=request.cookies.get('monash_session')
    session=db.get(BrowserSession,digest(token)) if token else None
    if not session or session.expires_at <= now():
        raise ApiError(401,'sign_in_required','Sign in to continue')
    if request.method not in {'GET','HEAD','OPTIONS'}:
        csrf=request.headers.get('X-CSRF-Token','')
        if not csrf or digest(csrf)!=session.csrf_hash or request.headers.get('Origin')!=settings.web_origin:
            raise ApiError(403,'csrf_rejected','Request origin or session proof is invalid')
    account=db.get(Account,session.account_id)
    if not account:
        raise ApiError(401,'invalid_session','Sign in again')
    account._mfa_verified=session.mfa_verified
    return account


def require_mfa(account: Account):
    if not getattr(account,'_mfa_verified',False):
        raise ApiError(403,'mfa_required','Use operator sign-in with multi-factor authentication')


def capability(name: str):
    def require(account: Account=Depends(require_account)) -> Account:
        if name not in account.capabilities:
            raise ApiError(403,'capability_required','This account is not permitted to perform this action')
        if name!='report:own':require_mfa(account)
        return account
    return require

require_citizen=capability('report:own')
require_reviewer=capability('report:review')
require_monitor=capability('monitor:read')
require_scenario=capability('scenario:operate')

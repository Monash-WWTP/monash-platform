"""OIDC authorization-code/PKCE browser login with database-held session state."""

import base64
import hashlib
import secrets
from datetime import timedelta
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..config import settings
from ..db.platform import BrowserSession, LoginAttempt, now
from ..db.session import get_db
from ..http.contracts import AccountSettingsView, AccountView
from ..http.errors import ApiError
from ..identity.dependencies import (
    account_from_claims,
    digest,
    require_account,
    signing_keys,
)
from ..identity.network import network_headers, network_url
from ..identity.tokens import validate_token

router = APIRouter(prefix="/auth", tags=["accounts"])


def discovery():
    try:
        response = httpx.get(
            network_url(settings.oidc_discovery_url),
            headers=network_headers(),
            timeout=5,
        )
        response.raise_for_status()
        metadata = response.json()
        if metadata.get("issuer") != settings.oidc_issuer:
            raise ValueError("Issuer mismatch")
        return metadata
    except (httpx.HTTPError, ValueError):
        raise ApiError(503, "identity_unavailable", "Identity service is unavailable")


@router.get("/login")
def login(
    operator: bool = False,
    account_settings: bool = False,
    db: Session = Depends(get_db),
):
    metadata = discovery()
    state, browser, verifier, nonce = [secrets.token_urlsafe(32) for _ in range(4)]
    db.add(
        LoginAttempt(
            state_hash=digest(state),
            browser_hash=digest(browser),
            verifier=verifier,
            nonce=nonce,
            operator_login=operator,
            expires_at=now() + timedelta(minutes=5),
        )
    )
    db.commit()
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .decode()
        .rstrip("=")
    )
    target = (
        metadata["authorization_endpoint"]
        + "?"
        + urlencode(
            dict(
                client_id=settings.oidc_operator_client_id
                if operator
                else settings.oidc_client_id,
                redirect_uri=settings.oidc_callback_url,
                response_type="code",
                scope="openid email profile",
                state=state,
                nonce=nonce,
                code_challenge=challenge,
                code_challenge_method="S256",
                **({"prompt": "login"} if operator else {}),
            )
        )
    )
    result = RedirectResponse(target, status_code=303)
    result.set_cookie(
        "monash_login",
        browser,
        httponly=True,
        secure=settings.session_secure,
        samesite="lax",
        max_age=300,
        path="/api/v1/auth",
    )
    if account_settings:
        result.set_cookie(
            "monash_account_return",
            "1",
            httponly=True,
            secure=settings.session_secure,
            samesite="lax",
            max_age=300,
            path="/api/v1/auth",
        )
    else:
        result.delete_cookie("monash_account_return", path="/api/v1/auth")
    return result


@router.get("/callback")
def callback(
    request: Request, code: str = "", state: str = "", db: Session = Depends(get_db)
):
    attempt = (
        db.query(LoginAttempt)
        .filter_by(state_hash=digest(state))
        .with_for_update()
        .first()
    )
    browser = request.cookies.get("monash_login", "")
    if (
        not attempt
        or attempt.expires_at <= now()
        or not browser
        or digest(browser) != attempt.browser_hash
    ):
        raise ApiError(
            400, "invalid_login", "Login expired or does not belong to this browser"
        )
    verifier, nonce = attempt.verifier, attempt.nonce
    client_id = (
        settings.oidc_operator_client_id
        if attempt.operator_login
        else settings.oidc_client_id
    )
    db.delete(attempt)
    db.commit()
    metadata = discovery()
    try:
        response = httpx.post(
            network_url(metadata["token_endpoint"]),
            headers=network_headers(),
            data=dict(
                grant_type="authorization_code",
                code=code,
                redirect_uri=settings.oidc_callback_url,
                client_id=client_id,
                client_secret=settings.oidc_client_secret,
                code_verifier=verifier,
            ),
            timeout=8,
        )
        response.raise_for_status()
        token = response.json()["id_token"]
        key = signing_keys(metadata["jwks_uri"]).get_signing_key_from_jwt(token).key
        claims = validate_token(token, key, settings.oidc_issuer, [client_id])
        if client_id == settings.oidc_operator_client_id and "mfa" not in claims.get(
            "amr", []
        ):
            raise ValueError("Operator MFA is required")
        if claims.get("nonce") != nonce:
            raise ValueError("Nonce mismatch")
    except (httpx.HTTPError, jwt.PyJWTError, ValueError, KeyError):
        raise ApiError(401, "invalid_login", "Unable to verify this login")
    account = account_from_claims(db, claims)
    token, csrf = secrets.token_urlsafe(48), secrets.token_urlsafe(32)
    db.add(
        BrowserSession(
            token_hash=digest(token),
            account_id=account.id,
            csrf_hash=digest(csrf),
            expires_at=now() + timedelta(minutes=30),
            mfa_verified="mfa" in claims.get("amr", []),
        )
    )
    db.commit()
    result = RedirectResponse(
        settings.web_origin
        + (
            "/account"
            if request.cookies.get("monash_account_return") == "1"
            else "/dashboard"
        ),
        status_code=303,
    )
    result.delete_cookie("monash_account_return", path="/api/v1/auth")
    result.delete_cookie("monash_login", path="/api/v1/auth")
    result.delete_cookie("monash_session", path="/api/v1")
    result.set_cookie(
        "monash_session",
        token,
        httponly=True,
        secure=settings.session_secure,
        samesite="lax",
        max_age=1800,
        path="/api",
    )
    # CSRF is intentionally browser-readable; identity/session tokens are not.
    result.set_cookie(
        "monash_csrf",
        csrf,
        secure=settings.session_secure,
        samesite="strict",
        max_age=1800,
        path="/",
    )
    return result


@router.get("/me", response_model=AccountView)
def me(account=Depends(require_account)):
    return {
        "display_name": account.display_name,
        "id": account.id,
        "email": account.email,
        "capabilities": account.capabilities,
    }


@router.post("/logout", status_code=204)
def logout(
    request: Request, account=Depends(require_account), db: Session = Depends(get_db)
):
    session = db.get(BrowserSession, digest(request.cookies.get("monash_session", "")))
    if session:
        db.delete(session)
        db.commit()
    result = JSONResponse(content=None, status_code=204)
    result.delete_cookie("monash_session", path="/api/v1")
    result.delete_cookie("monash_session", path="/api")
    result.delete_cookie("monash_csrf", path="/")
    result.headers["Cache-Control"] = "no-store"
    return result


@router.get("/register")
def register():
    return RedirectResponse(
        settings.oidc_issuer.rstrip("/")
        + "/if/flow/monash-citizen-enrollment/?"
        + urlencode({"next": settings.web_origin + "/api/v1/auth/login"}),
        status_code=303,
    )


@router.get("/account-settings", response_model=AccountSettingsView)
def account_settings(account=Depends(require_account)):
    from urllib.parse import urlsplit

    parsed = urlsplit(settings.oidc_issuer)
    loopback = (
        settings.app_env in {"development", "test", "staging"}
        and parsed.scheme == "http"
        and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    )
    if (
        not settings.account_settings_enabled
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
        or not (parsed.scheme == "https" or loopback)
    ):
        return {"available": False, "origin": None, "actions": {}}
    origin = f"{parsed.scheme}://{parsed.netloc}"
    paths = {
        "profile": "monash-account-profile",
        "email": "monash-account-email",
        "password": "monash-account-password",
        "security": "monash-account-security",
        "sessions": "monash-account-security",
        "signout_all": "monash-account-signout-all",
    }
    return {
        "available": True,
        "origin": origin,
        "actions": {
            key: origin + "/if/flow/" + slug + "/" for key, slug in paths.items()
        },
    }

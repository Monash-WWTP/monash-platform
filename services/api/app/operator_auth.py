"""Authentication dependency for WWTP operator-only API actions."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

_bearer = HTTPBearer(auto_error=False)


def require_operator(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """Validate the Supabase session with Auth and enforce the server allowlist."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Sign in with an approved operator account to perform this action.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    allowed_emails = settings.wwtp_operator_emails_list
    if not allowed_emails:
        raise HTTPException(
            status_code=503,
            detail="Operator access is not configured on this server.",
        )

    req = Request(
        f"{settings.supabase_url.rstrip('/')}/auth/v1/user",
        headers={
            "apikey": settings.supabase_key,
            "Authorization": f"Bearer {credentials.credentials}",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(req, timeout=8) as response:
            user = json.loads(response.read())
    except HTTPError as exc:
        if 400 <= exc.code < 500:
            raise HTTPException(
                status_code=401,
                detail="Your session is invalid or expired. Sign in again.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        raise HTTPException(status_code=503, detail="Authentication service is unavailable.") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise HTTPException(status_code=503, detail="Authentication service is unavailable.") from exc
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid authentication response.") from exc

    email = str(user.get("email") or "").strip().lower()
    if not email or not user.get("email_confirmed_at"):
        raise HTTPException(status_code=403, detail="A confirmed operator email is required.")
    if email not in allowed_emails:
        raise HTTPException(status_code=403, detail="This account is not approved for WWTP operations.")
    return email

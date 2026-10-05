"""Explicit private backchannel preserves the public OIDC issuer and redirect URLs."""

from urllib.parse import urlsplit, urlunsplit
from ..config import settings


def network_url(url: str) -> str:
    if not settings.oidc_backchannel_origin:
        return url
    parsed = urlsplit(url)
    public = urlsplit(settings.oidc_issuer)
    internal = urlsplit(settings.oidc_backchannel_origin)
    if parsed.netloc != public.netloc or parsed.scheme != public.scheme:
        raise ValueError("Identity endpoint is outside the configured issuer origin")
    return urlunsplit((internal.scheme, internal.netloc, parsed.path, parsed.query, ""))


def network_headers() -> dict:
    return (
        {"Host": urlsplit(settings.oidc_issuer).netloc}
        if settings.oidc_backchannel_origin
        else {}
    )

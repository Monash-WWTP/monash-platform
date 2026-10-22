from pydantic_settings import BaseSettings
from typing import Literal
from pydantic import model_validator
from urllib.parse import urlparse


class Settings(BaseSettings):
    database_url: str
    app_env: Literal["development", "test", "staging", "production"] = "development"
    # Comma-separated allowed origins in prod, e.g. "https://wwtp.vercel.app".
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    supabase_url: str = "https://eaxekwlmvpvftpgxiwlu.supabase.co"
    supabase_key: str = "sb_publishable_3-3Y9gvsPaJvErjgB80s6A__xFEcU1j"
    # Only these confirmed Supabase Auth users may change scenarios or run models.
    wwtp_operator_emails: str = ""

    account_settings_enabled: bool = False
    auth_mode: Literal["oidc"] = "oidc"
    oidc_issuer: str = ""
    oidc_backchannel_origin: str = ""
    identity_event_secret: str = ""
    oidc_discovery_url: str = ""
    oidc_jwks_url: str = ""
    oidc_mobile_issuer: str = ""
    oidc_client_id: str = "monash-web"
    oidc_operator_client_id: str = "monash-operator"
    oidc_mobile_client_id: str = "citizen-mobile"
    oidc_client_secret: str = ""
    oidc_callback_url: str = "http://localhost:8180/api/v1/auth/callback"
    web_origin: str = "http://localhost:8180"
    session_secure: bool = True
    storage_endpoint: str = ""
    storage_access_key: str = ""
    storage_secret_key: str = ""
    storage_bucket: str = "citizen-photos"
    storage_region: str = "garage"

    @model_validator(mode="after")
    def secure_production(self):
        if self.oidc_mobile_issuer and self.oidc_mobile_issuer != self.oidc_issuer:
            raise ValueError(
                "OIDC_MOBILE_ISSUER must match OIDC_ISSUER; a shared issuer is required"
            )
        if self.app_env == "production":
            if not self.identity_event_secret.strip():
                raise ValueError(
                    "Production requires identity_event_secret for session revocation"
                )
            if (
                self.auth_mode != "oidc"
                or not self.session_secure
                or not self.oidc_client_secret
            ):
                raise ValueError(
                    "Production requires native identity and secure sessions"
                )
            for value in (
                self.oidc_issuer,
                self.oidc_discovery_url,
                self.oidc_jwks_url,
                self.web_origin,
                self.oidc_callback_url,
            ):
                parsed = urlparse(value)
                if (
                    parsed.scheme != "https"
                    or not parsed.hostname
                    or parsed.hostname in {"localhost", "127.0.0.1", "::1"}
                    or parsed.username
                    or parsed.password
                ):
                    raise ValueError(
                        "Production identity and web URLs require public HTTPS"
                    )
            if "*" in self.cors_origins_list:
                raise ValueError("Production origins must be explicit")
            for origin in [self.web_origin, *self.cors_origins_list]:
                parsed = urlparse(origin)
                if (parsed.scheme != "https" or not parsed.hostname
                        or parsed.username or parsed.password
                        or parsed.path or parsed.params or parsed.query or parsed.fragment):
                    raise ValueError("Production web and CORS origins must be HTTPS origins without paths")
            callback = urlparse(self.oidc_callback_url)
            web = urlparse(self.web_origin)
            if ((callback.scheme, callback.netloc) != (web.scheme, web.netloc)
                    or callback.path != "/api/v1/auth/callback"
                    or callback.query or callback.fragment):
                raise ValueError("Production callback must use the web origin and /api/v1/auth/callback")
            if self.oidc_backchannel_origin:
                backchannel = urlparse(self.oidc_backchannel_origin)
                if (backchannel.scheme != "https" or not backchannel.hostname
                        or backchannel.username or backchannel.password
                        or backchannel.path or backchannel.params
                        or backchannel.query or backchannel.fragment):
                    raise ValueError("Production identity backchannel must be an HTTPS origin")
            if (
                not self.storage_endpoint
                or not self.storage_access_key
                or not self.storage_secret_key
            ):
                raise ValueError("Production private storage must be configured")
            storage = urlparse(self.storage_endpoint)
            if (storage.scheme != "https" or not storage.hostname
                    or storage.username or storage.password):
                raise ValueError("Production private storage requires HTTPS without URL credentials")
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def wwtp_operator_emails_list(self) -> set[str]:
        return {
            email.strip().lower()
            for email in self.wwtp_operator_emails.split(",")
            if email.strip()
        }


settings = Settings()

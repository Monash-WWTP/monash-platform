from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    database_url: str
    app_env: Literal["development", "test", "production"] = "development"
    # Comma-separated allowed origins in prod, e.g. "https://wwtp.vercel.app".
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    supabase_url: str = "https://eaxekwlmvpvftpgxiwlu.supabase.co"
    supabase_key: str = "sb_publishable_3-3Y9gvsPaJvErjgB80s6A__xFEcU1j"
    # Only these confirmed Supabase Auth users may change scenarios or run models.
    wwtp_operator_emails: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def wwtp_operator_emails_list(self) -> set[str]:
        return {email.strip().lower() for email in self.wwtp_operator_emails.split(",") if email.strip()}


settings = Settings()

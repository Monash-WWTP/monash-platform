"""Supported authentik custom-settings hook for account API guardrails."""

import sys

sys.path.insert(0, "/monash-brand")
MIDDLEWARE = ["account_settings.AccountSettingsGuard"]

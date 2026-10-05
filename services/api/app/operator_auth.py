"""Native application-owned operator authorization, keyed by stable account UUID."""

from fastapi import Depends
from .db.platform import Account
from .identity.dependencies import require_scenario, require_mfa
from .http.errors import ApiError


def require_operator(account: Account = Depends(require_scenario)) -> str:
    if "scenario:operate" not in account.capabilities:
        raise ApiError(403, "capability_required", "Operator access is required")
    require_mfa(account)
    return account.id

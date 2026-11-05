"""Research simulation access requires a verified signed-in platform account."""

from fastapi import Depends
from .db.platform import Account
from .identity.dependencies import require_account


def require_simulation_user(account: Account = Depends(require_account)) -> str:
    return account.id


# Compatibility for existing integrations/dependency overrides. Administrative,
# moderation and operator-response permissions have separate dependencies.
require_operator = require_simulation_user

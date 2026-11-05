from app.operator_auth import require_simulation_user
from app.db.platform import Account


def test_ordinary_account_can_access_simulation_without_operator_role_or_mfa():
    account = Account(id="citizen", capabilities=["report:own"])
    assert require_simulation_user(account) == "citizen"


def test_simulation_uses_stable_account_identifier_without_email_grants():
    account = Account(id="stable-id", email="not-an-authorization-key@example.test", capabilities=[])
    assert require_simulation_user(account) == "stable-id"

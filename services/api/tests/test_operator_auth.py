import pytest
from app.operator_auth import require_operator
from app.db.platform import Account
from app.http.errors import ApiError


def test_operator_requires_server_capability():
    with pytest.raises(ApiError):
        require_operator(Account(id="citizen", capabilities=["report:own"]))


def test_operator_requires_mfa():
    with pytest.raises(ApiError):
        require_operator(Account(id="operator", capabilities=["scenario:operate"]))


def test_operator_uses_stable_account_identifier():
    account = Account(
        id="stable-id",
        email="not-an-authorization-key@example.test",
        capabilities=["scenario:operate"],
    )
    account._mfa_verified = True
    assert require_operator(account) == "stable-id"

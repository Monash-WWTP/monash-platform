import importlib.util
from pathlib import Path
from types import SimpleNamespace

p = Path(__file__).resolve().parents[1] / 'infra/staging/identity/operator_mfa.py'
spec = importlib.util.spec_from_file_location('operator_mfa', p)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def needs_validation(context):
    scope = {}
    exec('def evaluate(request):\n' + '\n'.join('    ' + line for line in module.VALIDATION_NEEDED.splitlines()), scope)
    return scope['evaluate'](SimpleNamespace(context=context))


def test_setup_without_otp_proof_requires_validation():
    assert needs_validation({'flow_plan': SimpleNamespace(context={'auth_method_args': {'known_device': True}})})
    assert needs_validation({})


def test_successful_otp_validation_is_not_requested_twice():
    assert not needs_validation({'flow_plan': SimpleNamespace(context={'auth_method_args': {'mfa_devices': [object()]}})})


def test_operator_login_requires_fresh_authentication(monkeypatch):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from urllib.parse import parse_qs, urlsplit
    from app.db.models import Base
    from app.routers import auth
    monkeypatch.setattr(auth, 'discovery', lambda: {'authorization_endpoint': 'https://identity.example.test/authorize'})
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        response = auth.login(operator=True, account_settings=False, db=db)
        query = parse_qs(urlsplit(response.headers['location']).query)
        assert query['prompt'] == ['login']
        assert query['max_age'] == ['1']
        citizen = auth.login(operator=False, account_settings=False, db=db)
        assert 'max_age' not in parse_qs(urlsplit(citizen.headers['location']).query)

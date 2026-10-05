import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location(
    "backup", Path(__file__).resolve().parents[1] / "scripts/staging_backup.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_backup_authenticated_encryption_and_wrong_key():
    key = bytes(range(32))
    data = {"private": "never plaintext", "counts": {"samples": 154}}
    blob = module.seal(data, key)
    assert b"never plaintext" not in blob
    assert module.unseal(blob, key) == data
    for damaged, wrong_key in [
        (blob[:-1] + bytes([blob[-1] ^ 1]), key),
        (blob, bytes(32)),
    ]:
        with pytest.raises(Exception):
            module.unseal(damaged, wrong_key)


def test_restore_refuses_existing_staging_target():
    with pytest.raises(ValueError):
        module.validate_restore_name("monash-staging-database-1")
    with pytest.raises(ValueError):
        module.validate_restore_name("production")
    module.validate_restore_name("monash-restore-" + "a" * 12)

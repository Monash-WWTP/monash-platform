import importlib.util
import hashlib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def policy():
    spec = importlib.util.spec_from_file_location("repository_policy", ROOT / "scripts/check_repository.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_repository_has_complete_imports_and_documentation():
    policy().check(ROOT)


@pytest.mark.parametrize("path", ["apps/citizenflood/env.json", "local.sqlite", ".pytest_cache/state", "services/other/alembic.ini"])
def test_repository_rejects_credentials_generated_data_and_extra_migration_chain(tmp_path, path):
    with pytest.raises(ValueError):
        policy().check_paths([path])


def test_repository_rejects_private_credentials():
    with pytest.raises(ValueError):
        policy().check_content("settings.txt", "-----BEGIN " + "PRIVATE KEY-----")


def test_restricted_blob_cannot_be_imported_under_another_name():
    data = b"synthetic restricted material"
    with pytest.raises(ValueError):
        policy().check_restricted("renamed.csv", data, {hashlib.sha256(data).hexdigest()})


def test_inventory_can_validate_without_legacy_checkouts():
    import subprocess
    import sys
    result = subprocess.run([sys.executable, str(ROOT / "scripts/check_import_inventory.py"), "--verify-targets"],
                            cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr

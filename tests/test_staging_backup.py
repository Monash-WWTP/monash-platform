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


def test_restore_waits_past_temporary_initialization_server(monkeypatch, tmp_path):
    """The image's Unix-only initialization server is not a restore-ready target."""
    import base64
    import hashlib
    from types import SimpleNamespace

    (tmp_path / 'infra/staging').mkdir(parents=True)
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    dump = b'synthetic dump'
    data = {
        'version': 1,
        'databases': {'application': {
            'dump': base64.b64encode(dump).decode(),
            'sha256': hashlib.sha256(dump).hexdigest(),
            'manifest': [],
        }},
        'objects': [],
        'configuration': {'env': ''},
    }
    monkeypatch.setattr(module, 'private_file', lambda path: b'encrypted fixture')
    monkeypatch.setattr(module, 'unseal', lambda blob, key: data)
    monkeypatch.setattr(module, 'database_manifest', lambda *args: [])
    monkeypatch.setattr(module.time, 'sleep', lambda seconds: None)
    monkeypatch.setattr(module, 'storage', lambda values: SimpleNamespace(
        create_bucket=lambda **kwargs: None, delete_bucket=lambda **kwargs: None))
    final_server = False
    tcp_probes = 0

    def probe(args, **kwargs):
        nonlocal final_server, tcp_probes
        # The temporary server reports Unix readiness, but has no TCP listener.
        if '-h' not in args:
            return SimpleNamespace(returncode=0)
        tcp_probes += 1
        final_server = tcp_probes > 1
        return SimpleNamespace(returncode=0 if final_server else 1)

    def run(args, input=None):
        if 'pg_restore' in args:
            assert final_server, 'Restore began on the temporary initialization server'
        return b''

    monkeypatch.setattr(module.subprocess, 'run', probe)
    monkeypatch.setattr(module, 'run', run)
    module.rehearse(tmp_path / 'backup.enc', bytes(32))
    assert tcp_probes == 2


@pytest.mark.parametrize("limit", [8, 100])
def test_backup_reads_objects_with_a_bound_and_closes_response(monkeypatch, tmp_path, limit):
    from io import BytesIO
    from types import SimpleNamespace

    class BoundedBody(BytesIO):
        def read(self, size=-1):
            assert size >= 0, 'Backup must bound reads before allocating object bytes'
            return super().read(size)

    monkeypatch.setattr(module, 'MAX_BACKUP_OBJECT_BYTES', limit)
    body = BoundedBody(b'synthetic photo')
    store = SimpleNamespace(
        get_paginator=lambda name: SimpleNamespace(paginate=lambda **kwargs: [
            {'Contents': [{'Key': 'fixture/photo'}]}]),
        get_object=lambda **kwargs: {'Body': body},
    )
    monkeypatch.setattr(module, 'storage', lambda values: store)
    monkeypatch.setattr(module, 'private_file', lambda path: b'SYNTHETIC=value\n')
    monkeypatch.setattr(module, 'run', lambda args: b'synthetic dump')
    monkeypatch.setattr(module, 'database_manifest', lambda *args: [])
    output = tmp_path / 'backup.enc'
    if limit < len(b'synthetic photo'):
        with pytest.raises(ValueError, match='exceeds'):
            module.backup(output, bytes(32))
        assert body.closed
        assert not output.exists()
        return
    module.backup(output, bytes(32))
    assert body.closed
    saved = module.unseal(output.read_bytes(), bytes(32))
    assert len(saved['objects']) == 1

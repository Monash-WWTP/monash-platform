"""Check tracked/imported paths, private credential patterns, and onboarding links."""
import re
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DOCS = (
    "docs/operations/local-development.md", "docs/api/README.md",
    "docs/science/VALIDATION.md", "docs/operations/deployment.md",
    "apps/citizenflood/README.md", "apps/dashboard/README.md",
)


def check_paths(paths):
    for name in paths:
        path = Path(name)
        if path.name == "env.json" or path.suffix in {".db", ".sqlite", ".sqlite3", ".parquet", ".keystore", ".jks"}:
            raise ValueError(f"private or generated file: {name}")
        if any(part in {".venv", "node_modules", ".dart_tool", ".pytest_cache", "__pycache__", "build", "dist"} for part in path.parts):
            raise ValueError(f"cache/build output: {name}")
        if path.name == "alembic.ini" and name != "services/api/alembic.ini":
            raise ValueError(f"extra active migration chain: {name}")
        if "supabase" in path.parts and not name.startswith("legacy/"):
            raise ValueError(f"Supabase migrations must be inactive legacy references: {name}")
        if path.name.startswith(".env") and path.name not in {".env.example", ".env.sample"}:
            raise ValueError(f"private environment file: {name}")


def check_content(name, content):
    patterns = (r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", r"\bgh[pousr]_[A-Za-z0-9]{20,}", r"\bsb_secret_[A-Za-z0-9_-]{20,}")
    if any(re.search(pattern, content) for pattern in patterns):
        raise ValueError(f"private credential pattern: {name}")


def check_restricted(name, data, restricted_hashes):
    if hashlib.sha256(data).hexdigest() in restricted_hashes:
        raise ValueError(f"restricted source blob: {name}")


def check(root=ROOT):
    paths = subprocess.check_output(["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"]).decode().split("\0")
    paths = [p for p in paths if p]
    check_paths(paths)
    assert "services/api/alembic.ini" in paths, "missing active migration configuration"
    inventory = json.loads((root / "docs/migration/source-inventory.json").read_text())
    restricted_hashes = {r["source_sha256"] for r in inventory["files"] if r["disposition"] == "restricted"}
    for name in paths:
        data = (root / name).read_bytes()
        check_restricted(name, data, restricted_hashes)
        if b"\0" not in data:
            check_content(name, data.decode("utf-8", "replace"))
    readme = (root / "README.md").read_text()
    for name in REQUIRED_DOCS:
        assert name in readme and (root / name).is_file(), f"missing onboarding link: {name}"
    print(f"repository policy passed: {len(paths)} files")


if __name__ == "__main__":
    check()

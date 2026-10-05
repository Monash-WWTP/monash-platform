"""Initialize isolated local staging secrets; never overwrites existing custody."""

from pathlib import Path
import secrets
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "infra/staging/.env.local"


def main():
    if not ENV.exists():
        values = {
            name: secrets.token_hex(32)
            for name in (
                "APP_DB_PASSWORD",
                "IDENTITY_DB_PASSWORD",
                "IDENTITY_SECRET",
                "IDENTITY_ADMIN_PASSWORD",
                "IDENTITY_BOOTSTRAP_TOKEN",
                "STORAGE_SECRET_KEY",
                "MONASH_WEB_SECRET",
            )
        }
        values["STORAGE_ACCESS_KEY"] = "GK" + secrets.token_hex(16)
        ENV.parent.mkdir(parents=True, exist_ok=True)
        with ENV.open("x") as stream:
            ENV.chmod(0o600)
            stream.write("".join(f"{key}={value}\n" for key, value in values.items()))
    if ENV.stat().st_mode & 0o077:
        raise ValueError("Local secrets must have owner-only permissions")
    values = dict(
        line.split("=", 1)
        for line in ENV.read_text().splitlines()
        if line and not line.startswith("#")
    )
    if "IDENTITY_EVENT_SECRET" not in values:
        with ENV.open("a") as stream:
            stream.write("IDENTITY_EVENT_SECRET=" + secrets.token_hex(32) + "\n")
    garage = ENV.parent / "garage.toml.local"
    if not garage.exists():
        with garage.open("x") as stream:
            garage.chmod(0o600)
            stream.write(
                (ENV.parent / "garage.toml")
                .read_text()
                .replace("GENERATED_BY_STAGING", secrets.token_hex(32))
            )
    command = [
        "docker",
        "compose",
        "--env-file",
        str(ENV),
        "-f",
        str(ROOT / "infra/staging/compose.yaml"),
    ]
    subprocess.run(command + sys.argv[1:], check=True)


if __name__ == "__main__":
    main()

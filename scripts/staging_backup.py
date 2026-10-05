"""Encrypted local backup and isolated restore rehearsal; never restores over staging."""

import argparse, base64, hashlib, json, os, re, secrets, subprocess, time
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import boto3
from botocore.config import Config

ROOT = Path(__file__).resolve().parents[1]
MAGIC = b"MONASHBACKUP1"


def seal(data, key):
    nonce = os.urandom(12)
    return (
        MAGIC
        + nonce
        + AESGCM(key).encrypt(nonce, json.dumps(data, sort_keys=True).encode(), MAGIC)
    )


def unseal(blob, key):
    if not blob.startswith(MAGIC):
        raise ValueError("Unsupported backup envelope")
    return json.loads(
        AESGCM(key).decrypt(
            blob[len(MAGIC) : len(MAGIC) + 12], blob[len(MAGIC) + 12 :], MAGIC
        )
    )


def validate_restore_name(name):
    if not re.fullmatch(r"monash-restore-[a-f0-9]{12}", name):
        raise ValueError("Restore target must be a new isolated rehearsal container")


def run(args, input=None):
    return subprocess.run(
        args, input=input, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
    ).stdout


def database_manifest(container, user, database):
    def query(sql):
        return (
            run(
                [
                    "docker",
                    "exec",
                    "-i",
                    container,
                    "psql",
                    "-X",
                    "-A",
                    "-t",
                    "-v",
                    "ON_ERROR_STOP=1",
                    "-U",
                    user,
                    "-d",
                    database,
                ],
                sql.encode(),
            )
            .decode()
            .strip()
        )

    tables = query(
        "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
    ).splitlines()
    # Identifiers originate from PostgreSQL, always quote even though controlled.
    statements = []
    for table in tables:
        quoted = '"' + table.replace('"', '""') + '"'
        literal = "'" + table.replace("'", "''") + "'"
        statements.append(
            "SELECT json_build_object('table',"
            + literal
            + ",'count',count(*),'sha',md5(COALESCE(jsonb_agg(to_jsonb(t) ORDER BY to_jsonb(t)::text)::text,''))) FROM "
            + quoted
            + " t"
        )
    return [json.loads(line) for line in query(";\n".join(statements)).splitlines()]


def private_file(path):
    if path.stat().st_mode & 0o077:
        raise ValueError("Private custody requires owner-only permissions")
    return path.read_bytes()


def key_at(path):
    if path.resolve().is_relative_to(ROOT):
        raise ValueError("Backup key must remain outside the repository")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with path.open("xb") as stream:
            path.chmod(0o600)
            stream.write(os.urandom(32))
    key = private_file(path)
    if len(key) != 32:
        raise ValueError("Invalid backup key")
    return key


def storage(values):
    return boto3.client(
        "s3",
        endpoint_url="http://127.0.0.1:3900",
        aws_access_key_id=values["STORAGE_ACCESS_KEY"],
        aws_secret_access_key=values["STORAGE_SECRET_KEY"],
        region_name="garage",
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            connect_timeout=3,
            read_timeout=15,
        ),
    )


def backup(destination, key):
    env = private_file(ROOT / "infra/staging/.env.local").decode()
    values = dict(
        line.split("=", 1)
        for line in env.splitlines()
        if line and not line.startswith("#")
    )
    records = {}
    for label, container, user, database in [
        ("application", "monash-staging-database-1", "monash", "monash"),
        ("identity", "monash-staging-identity-db-1", "authentik", "authentik"),
    ]:
        blob = run(
            [
                "docker",
                "exec",
                container,
                "pg_dump",
                "-U",
                user,
                "-d",
                database,
                "--format=custom",
                "--no-owner",
                "--no-acl",
            ]
        )
        records[label] = {
            "dump": base64.b64encode(blob).decode(),
            "sha256": hashlib.sha256(blob).hexdigest(),
            "manifest": database_manifest(container, user, database),
        }
    client = storage(values)
    objects = []
    total = 0
    for page in client.get_paginator("list_objects_v2").paginate(
        Bucket="citizen-photos"
    ):
        for item in page.get("Contents", []):
            data = client.get_object(Bucket="citizen-photos", Key=item["Key"])[
                "Body"
            ].read()
            total += len(data)
            if total > 256 * 1024 * 1024:
                raise ValueError(
                    "Local rehearsal backup exceeds 256 MB; use streaming production backup"
                )
            objects.append(
                {
                    "key": item["Key"],
                    "content": base64.b64encode(data).decode(),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )
    config = {
        "env": env,
        "garage": private_file(ROOT / "infra/staging/garage.toml.local").decode(),
    }
    envelope = seal(
        {
            "version": 1,
            "created_at": time.time(),
            "databases": records,
            "objects": objects,
            "configuration": config,
        },
        key,
    )
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with destination.open("xb") as stream:
        destination.chmod(0o600)
        stream.write(envelope)
    print(
        json.dumps(
            {
                "backup": str(destination),
                "sha256": hashlib.sha256(envelope).hexdigest(),
                "objects": len(objects),
                "application_tables": len(records["application"]["manifest"]),
                "identity_tables": len(records["identity"]["manifest"]),
            }
        )
    )


def rehearse(source, key):
    data = unseal(private_file(source), key)
    if data.get("version") != 1:
        raise ValueError("Unsupported backup version")
    # Authenticate/check all bytes before starting a restore.
    for record in data["databases"].values():
        if (
            hashlib.sha256(base64.b64decode(record["dump"])).hexdigest()
            != record["sha256"]
        ):
            raise ValueError("Database checksum failed")
    for item in data["objects"]:
        if (
            hashlib.sha256(base64.b64decode(item["content"])).hexdigest()
            != item["sha256"]
        ):
            raise ValueError("Media checksum failed")
    restored = []
    for label, record in data["databases"].items():
        name = "monash-restore-" + secrets.token_hex(6)
        validate_restore_name(name)
        password = secrets.token_urlsafe(32)
        # Secret is supplied on stdin, not the command line.
        envfile = (
            ROOT / "infra/staging" / ("restore-" + secrets.token_hex(6) + ".local")
        )
        with envfile.open("x") as stream:
            envfile.chmod(0o600)
            stream.write("POSTGRES_PASSWORD=" + password + "\nPOSTGRES_DB=restore\n")
        created = False
        try:
            run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    name,
                    "--label",
                    "monash.restore-rehearsal=true",
                    "--env-file",
                    str(envfile),
                    "postgres:16.13",
                ]
            )
            created = True
            for _ in range(60):
                ready = subprocess.run(
                    [
                        "docker",
                        "exec",
                        name,
                        "pg_isready",
                        "-U",
                        "postgres",
                        "-d",
                        "restore",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                if ready.returncode == 0:
                    break
                time.sleep(0.5)
            else:
                raise RuntimeError("Restore database did not become ready")
            run(
                [
                    "docker",
                    "exec",
                    "-i",
                    name,
                    "pg_restore",
                    "-U",
                    "postgres",
                    "-d",
                    "restore",
                    "--no-owner",
                    "--no-acl",
                    "--exit-on-error",
                ],
                base64.b64decode(record["dump"]),
            )
            actual = database_manifest(name, "postgres", "restore")
            if actual != record["manifest"]:
                raise ValueError("Restored table reconciliation failed: " + label)
            restored.append(
                {"database": label, "tables": len(actual), "reconciled": True}
            )
        finally:
            envfile.unlink(missing_ok=True)
            if created:
                run(["docker", "rm", "-f", "-v", name])
    # Private objects are restored to a separate temporary bucket, never over source keys.
    values = dict(
        line.split("=", 1)
        for line in data["configuration"]["env"].splitlines()
        if line and not line.startswith("#")
    )
    client = storage(values)
    bucket = "monash-restore-" + secrets.token_hex(6)
    client.create_bucket(Bucket=bucket)
    keys = []
    try:
        for item in data["objects"]:
            value = base64.b64decode(item["content"])
            client.put_object(Bucket=bucket, Key=item["key"], Body=value)
            keys.append(item["key"])
            actual = client.get_object(Bucket=bucket, Key=item["key"])["Body"].read()
            if hashlib.sha256(actual).hexdigest() != item["sha256"]:
                raise ValueError("Restored media reconciliation failed")
    finally:
        for object_key in keys:
            client.delete_object(Bucket=bucket, Key=object_key)
        client.delete_bucket(Bucket=bucket)
    print(
        json.dumps(
            {
                "restored": restored,
                "media_objects": len(keys),
                "configuration_authenticated": True,
                "source_unchanged": True,
            }
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["backup", "rehearse"])
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument(
        "--key",
        type=Path,
        default=Path.home() / ".local/share/monash-platform/staging-backup.key",
    )
    args = parser.parse_args()
    key = key_at(args.key)
    if args.action == "backup":
        backup(args.file, key)
    else:
        rehearse(args.file, key)


if __name__ == "__main__":
    main()

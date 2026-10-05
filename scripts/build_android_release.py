"""Build and verify a directly distributable CitizenFlood APK with private signing inputs."""

import argparse
import base64
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def validate_client_config(config):
    allowed = {
        "API_BASE_URL",
        "OIDC_ISSUER",
        "OIDC_DISCOVERY_URL",
        "OIDC_CLIENT_ID",
        "LOCAL_STAGING",
    }
    if set(config) - allowed or config.get("LOCAL_STAGING") not in (
        False,
        "false",
        None,
    ):
        raise ValueError("Release accepts public native client configuration only")
    urls = {}
    for name in ("API_BASE_URL", "OIDC_ISSUER", "OIDC_DISCOVERY_URL"):
        parsed = urlparse(config.get(name, ""))
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.hostname
            in {"localhost", "127.0.0.1", "::1", "example.com", "example.supabase.co"}
            or parsed.hostname.endswith(".localhost")
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Release requires real public HTTPS API and identity URLs")
        urls[name] = parsed
    if urls["API_BASE_URL"].path not in ("", "/"):
        raise ValueError("API configuration must be an origin")
    if urls["OIDC_ISSUER"].netloc != urls["OIDC_DISCOVERY_URL"].netloc:
        raise ValueError("Discovery must use the configured identity origin")
    if not config.get("OIDC_CLIENT_ID") or not urls["OIDC_DISCOVERY_URL"].path.endswith(
        "/.well-known/openid-configuration"
    ):
        raise ValueError("Public OIDC client and discovery path are required")
    return config["API_BASE_URL"].rstrip("/")


def validate_signer(output, expected):
    digests = re.findall(r"certificate SHA-256 digest:\s*([a-fA-F0-9]{64})", output)
    if (
        "Android Debug" in output
        or len(digests) != 1
        or digests[0].lower() != expected.lower()
    ):
        raise ValueError("APK must use the expected project release signing identity.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--signing-dir", type=Path, required=True)
    parser.add_argument("--flutter", type=Path, required=True)
    parser.add_argument("--android-sdk", type=Path, required=True)
    parser.add_argument("--java-home", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--version-code", type=int, required=True)
    parser.add_argument("--artifact-url", required=True)
    parser.add_argument("--published-at", type=date.fromisoformat, required=True)
    args = parser.parse_args()
    backend = validate_client_config(json.loads(args.config.read_text()))
    if not re.fullmatch(r"\d+\.\d+\.\d+", args.version) or args.version_code < 1:
        raise ValueError("Release requires semantic version and positive version code.")
    parsed = urlparse(args.artifact_url)
    if (
        parsed.scheme != "https"
        or parsed.username
        or parsed.password
        or not parsed.path.endswith(".apk")
    ):
        raise ValueError("Release requires a public HTTPS APK URL.")
    signing = args.signing_dir.resolve()
    if signing.is_relative_to(ROOT):
        raise ValueError("Signing material must stay outside the repository.")
    password_file = signing / "release-password"
    keystore = signing / "citizenflood-release.jks"
    for path in (signing, password_file, keystore):
        if not path.exists() or path.stat().st_mode & 0o077:
            raise ValueError("Signing material must exist with owner-only permissions.")
    if not (args.java_home / "bin/java").is_file():
        raise ValueError("Java home must contain bin/java.")
    env = dict(os.environ)
    env.update(
        JAVA_HOME=str(args.java_home.resolve()),
        PATH=str(args.java_home.resolve() / "bin") + os.pathsep + env.get("PATH", ""),
    )
    env.update(
        CITIZENFLOOD_KEYSTORE=str(keystore),
        CITIZENFLOOD_KEY_ALIAS="citizenflood-release",
        CITIZENFLOOD_STORE_PASSWORD=password_file.read_text().strip(),
        CITIZENFLOOD_KEY_PASSWORD=password_file.read_text().strip(),
        ANDROID_HOME=str(args.android_sdk),
    )
    version = subprocess.check_output(
        [str(args.flutter), "--version"], env=env, text=True
    )
    if "Flutter 3.44.7 " not in version:
        raise ValueError("Use the verified Flutter 3.44.7 release toolchain.")
    app = ROOT / "apps/citizenflood"
    subprocess.run(
        [str(args.flutter), "pub", "get", "--enforce-lockfile"],
        cwd=app,
        env=env,
        check=True,
    )
    subprocess.run(
        [
            str(args.flutter),
            "build",
            "apk",
            "--release",
            "--dart-define-from-file=" + str(args.config.resolve()),
            "--build-name=" + args.version,
            "--build-number=" + str(args.version_code),
        ],
        cwd=app,
        env=env,
        check=True,
    )
    apk = app / "build/app/outputs/flutter-apk/app-release.apk"
    tools = args.android_sdk / "build-tools/36.0.0"
    result = subprocess.check_output(
        [str(tools / "apksigner"), "verify", "--verbose", "--print-certs", str(apk)],
        env=env,
        text=True,
    )
    expected = (signing / "certificate-sha256").read_text().strip()
    validate_signer(result, expected)
    badging = subprocess.check_output(
        [str(tools / "aapt"), "dump", "badging", str(apk)], env=env, text=True
    )
    package = re.search(
        r"package: name='([^']+)' versionCode='([^']+)' versionName='([^']+)'", badging
    )
    if not package or package.groups() != (
        "au.edu.monash.citizenflood",
        str(args.version_code),
        args.version,
    ):
        raise ValueError("Built APK metadata does not match the intended release.")
    sdk = int(re.search(r"sdkVersion:'(\d+)'", badging)[1])
    android_versions = {
        23: "6.0",
        24: "7.0",
        25: "7.1",
        26: "8.0",
        27: "8.1",
        28: "9.0",
        29: "10.0",
        30: "11.0",
        31: "12.0",
        32: "12.1",
        33: "13.0",
        34: "14.0",
        35: "15.0",
        36: "16.0",
    }
    metadata = dict(
        versionName=args.version,
        versionCode=args.version_code,
        minAndroid=android_versions[sdk],
        publishedAt=args.published_at.isoformat(),
        byteSize=apk.stat().st_size,
        sha256=hashlib.sha256(apk.read_bytes()).hexdigest(),
        artifactUrl=args.artifact_url,
        notes=[
            "Signed native Android client for the shared platform API.",
            "Verified accounts are shared with the dashboard; citizen reports require sign-in.",
        ],
    )
    out = app / "build/release-manifest.json"
    out.write_text(json.dumps(metadata, indent=2) + "\n")
    print(
        json.dumps(
            {
                "apk": str(apk),
                "manifest": str(out),
                "backend": backend,
                "certificateSha256": expected,
                "minSdk": sdk,
            }
        )
    )


if __name__ == "__main__":
    main()

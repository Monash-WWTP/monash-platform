# CitizenFlood direct APK distribution

Google Play listing is optional for this distribution path. The project builds a signed APK and hosts it over HTTPS; visitors download it and approve Android's installation prompt. Signing identifies the publisher and enables updates signed by the same key. It does not certify scientific validity or constitute Google verification.

## Current release configuration

The user authorized the existing real Supabase backend during standalone API development. Its origin is `https://eaxekwlmvpvftpgxiwlu.supabase.co`; the app receives its public/publishable client key at build time. APK values are extractable. Never supply service-role keys, database credentials or private signing inputs as Dart defines.

Anonymous reporting and optional email sign-in remain legacy CitizenFlood behavior. The future shared verified account/standalone API flows are not included in this release. No invented observations or measurements are seeded. Production build configuration is read from the existing ignored legacy `env.json`; the release script rejects placeholder origins and private server keys. Unit/CI fixtures remain isolated from distributable builds and operational data.

## Signing custody

A new project-specific RSA release key is held locally at `/home/jienweng/.local/share/monash-platform/signing/`, outside all Git repositories, with owner-only permissions. The keystore is `citizenflood-release.jks`, alias `citizenflood-release`. Its password is in the owner-only `release-password` file. `certificate-sha256` contains the public signing certificate fingerprint. Secrets are not printed, embedded in the app, pushed to Git or put in CI.

The owner must keep a secure independent backup of the keystore, password and alias before relying on long-term updates. The current directory is local custody, **not** an independently verified backup. Losing the signing identity can prevent updates to installed copies. Do not regenerate or replace this key during routine builds.

An installed development APK signed with Android's debug key cannot be updated with the new project key. Such users must remove the development copy and install the release. Removing it clears local app/session state; authenticated server records are not deleted by uninstalling the APK. Preserve useful account access before replacing a development installation.

## Build and verify

Use the isolated verified Flutter 3.44.7 SDK; Android build tools 36.0.0. Build inputs are pinned and `flutter pub get --enforce-lockfile` prevents silent dependency changes.

```sh
uv run --locked python scripts/build_android_release.py \
  --config /home/jienweng/projects/citizenflood/env.json \
  --signing-dir /home/jienweng/.local/share/monash-platform/signing \
  --flutter /home/jienweng/.cache/monash-platform/flutter-3.44.7/bin/flutter \
  --android-sdk /home/jienweng/Android/Sdk \
  --java-home /home/jienweng/Applications/android-studio/jbr \
  --version 1.0.0 --version-code 2 --published-at 2026-10-03 \
  --artifact-url https://monash-citizenflood-downloads.vercel.app/releases/1.0.0-2/citizenflood.apk
```

Gradle's resolved app task graph refuses release tasks when project signing inputs are absent, including generic `assemble`/`build` entry points. Debug CI can still compile without the release key. The builder verifies the APK signature and exact project certificate, package ID, version, minimum Android API, byte size and SHA-256. A build alone does not demonstrate launch, backend behavior or successful user installation.

## Publication

APK hosting is a separate static Vercel project (`monash-citizenflood-downloads`); the website remains `monash-water-platform`. Use immutable version paths, retain prior artifacts for updates/rollback, and serve the APK directly with attachment and package MIME headers. No Vercel Function proxies the file. Move these files to independent object storage or a standalone HTTPS server later without changing signing identity.

After signature/runtime/download verification, add the derived manifest to the dashboard release module and deploy the website. Verify an unauthenticated download's size and SHA-256 match the local verified APK before enabling the installation button. Future releases need increasing versionCode, the same signer, install/update checks and accurate release notes.

Current Android developer-verification and device-policy requirements can affect installation by target region. Follow official installation prompts; signing does not bypass verification, Play Protect or managed-device restrictions.

Sources: [Flutter Android release](https://docs.flutter.dev/deployment/android), [Android signing](https://developer.android.com/studio/publish/app-signing), [Android developer verification](https://developer.android.com/developer-verification/guides).

## Verification record, 2026-10-03

The signed version 1.0.0 (versionCode 2) built successfully with Flutter 3.44.7. Signature, exact release certificate, package/version/minimum API and derived checksum passed. Generic unsigned release task selection failed as intended; debug task selection remained available. All 65 Python tests and 9 dashboard tests passed, with lint/build and the public portal browser contract passing. A fresh review found no remaining material code defects. Android runtime and hosted download evidence are recorded in the release record after those checks finish.

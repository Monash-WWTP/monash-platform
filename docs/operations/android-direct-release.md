# CitizenFlood direct APK distribution

Google Play listing is optional for this distribution path. The project builds a signed APK and hosts it over HTTPS; visitors download it and approve Android's installation prompt. Signing identifies the publisher and enables updates signed by the same key. It does not certify scientific validity or constitute Google verification.

## Published legacy release (historical record)

The user authorized the existing real Supabase backend during standalone API development. Its origin is `https://eaxekwlmvpvftpgxiwlu.supabase.co`; the app receives its public/publishable client key at build time. APK values are extractable. Never supply service-role keys, database credentials or private signing inputs as Dart defines.

Anonymous reporting and optional email sign-in remain legacy CitizenFlood behavior. The future shared verified account/standalone API flows are not included in this release. No invented observations or measurements are seeded. Production build configuration is read from the existing ignored legacy `env.json`; the release script rejects placeholder origins and private server keys. Unit/CI fixtures remain isolated from distributable builds and operational data.

## Signing custody

A new project-specific RSA release key is held locally at `/home/jienweng/.local/share/monash-platform/signing/`, outside all Git repositories, with owner-only permissions. The keystore is `citizenflood-release.jks`, alias `citizenflood-release`. Its password is in the owner-only `release-password` file. `certificate-sha256` contains the public signing certificate fingerprint. Secrets are not printed, embedded in the app, pushed to Git or put in CI.

The owner must keep a secure independent backup of the keystore, password and alias before relying on long-term updates. The current directory is local custody, **not** an independently verified backup. Losing the signing identity can prevent updates to installed copies. Do not regenerate or replace this key during routine builds.

An installed development APK signed with Android's debug key cannot be updated with the new project key. Such users must remove the development copy and install the release. Removing it clears local app/session state; authenticated server records are not deleted by uninstalling the APK. Preserve useful account access before replacing a development installation.

## Build and verify the next API-connected release

Use the isolated verified Flutter 3.44.7 SDK; Android build tools 36.0.0. Build inputs are pinned and `flutter pub get --enforce-lockfile` prevents silent dependency changes.

The current source requires the successor API and identity configuration. The old Supabase `env.json` is only a historical release input and is rejected by the current builder. Deploy and qualify the backend first; compile a debug preview against local staging for development only.

Save the following **public client configuration** outside Git, replacing every example URL with the approved deployed service. Its issuer must equal the API's shared issuer; obtain discovery metadata from the actual mobile provider. No client secret belongs in this file.

```json
{
  "API_BASE_URL": "https://api.example.com",
  "OIDC_ISSUER": "https://accounts.example.com/",
  "OIDC_DISCOVERY_URL": "https://accounts.example.com/application/o/citizen-mobile/.well-known/openid-configuration",
  "OIDC_CLIENT_ID": "citizen-mobile",
  "LOCAL_STAGING": false
}
```

Example command for the next candidate, after configuration and acceptance are complete (the placeholder URL is not a published artifact):

```sh
uv run --locked python scripts/build_android_release.py \
  --config /srv/monash/private/mobile-client.json \
  --signing-dir /home/jienweng/.local/share/monash-platform/signing \
  --flutter /home/jienweng/.cache/monash-platform/flutter-3.44.7/bin/flutter \
  --android-sdk /home/jienweng/Android/Sdk \
  --java-home /home/jienweng/Applications/android-studio/jbr \
  --version 1.0.1 --version-code 3 --published-at YYYY-MM-DD \
  --artifact-url https://downloads.example.com/releases/1.0.1-3/citizenflood.apk
```

Choose the actual release date and immutable artifact URL. The builder requires a versionCode greater than the dashboard's currently published code (2); update the candidate's name/code if another release has since shipped. Preserve the existing signing identity. Do not overwrite the public manifest/download until signature, runtime, fresh-install/upgrade, account-switch privacy, location, report/photo retry and backend acceptance all pass. Historical 1.0.0/code 2 evidence remains in `android-release-1.0.0.json`; reproduce it only from its historical source/tooling revision.


Gradle's resolved app task graph refuses release tasks when project signing inputs are absent, including generic `assemble`/`build` entry points. Debug CI can still compile without the release key. The builder verifies the APK signature and exact project certificate, package ID, version, minimum Android API, byte size and SHA-256. A build alone does not demonstrate launch, backend behavior or successful user installation.

## Publication

APK hosting is a separate static Vercel project (`monash-citizenflood-downloads`); the website remains `monash-water-platform`. Use immutable version paths, retain prior artifacts for updates/rollback, and serve the APK directly with attachment and package MIME headers. No Vercel Function proxies the file. Move these files to independent object storage or a standalone HTTPS server later without changing signing identity.

After signature/runtime/download verification, add the derived manifest to the dashboard release module and deploy the website. Verify an unauthenticated download's size and SHA-256 match the local verified APK before enabling the installation button. Future releases need increasing versionCode, the same signer, install/update checks and accurate release notes.

Current Android developer-verification and device-policy requirements can affect installation by target region. Follow official installation prompts; signing does not bypass verification, Play Protect or managed-device restrictions.

Sources: [Flutter Android release](https://docs.flutter.dev/deployment/android), [Android signing](https://developer.android.com/studio/publish/app-signing), [Android developer verification](https://developer.android.com/developer-verification/guides).

## Verification record, 2026-10-03

The signed version 1.0.0 (versionCode 2) built successfully with Flutter 3.44.7. Signature, exact release certificate, package/version/minimum API and derived checksum passed. Generic unsigned release task selection failed as intended; debug task selection remained available. All 65 Python tests and 9 dashboard tests passed, with lint/build and the public portal browser contract passing. A fresh review found no remaining material code defects. Android runtime and hosted download evidence are recorded in the release record after those checks finish.

# Verified local toolchains

The CitizenFlood import was checked on 2026-10-02 using the official Flutter
3.44.7 stable Linux SDK (framework revision `84fc5cbb22`, Dart 3.12.2,
DevTools 2.57.0). Its release archive SHA-256 was verified against Flutter's
release index: `a0edd646c159c0e816788c0e46a4f071199c1320495898f5a679599b583a05a4`.
The local Android SDK has platforms 35 and 36 and build-tools 36.0.0. The
local JDK is Android Studio's JBR 25.0.3; CI uses Temurin 17.

Mobile verification commands from `apps/citizenflood`:

```sh
flutter pub get
flutter analyze
flutter test
flutter build apk --debug \
  --dart-define=SUPABASE_URL=https://example.supabase.co \
  --dart-define=SUPABASE_ANON_KEY=synthetic-ci-key
test -s build/app/outputs/flutter-apk/app-debug.apk
```

Synthetic values are only for a build check; the resulting APK is not an
operational client. Do not use production signing keys or credentials in CI.

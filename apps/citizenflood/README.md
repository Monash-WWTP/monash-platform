# CitizenFlood

Flutter mobile app for citizen flood, rain, water-level and wastewater observations. It retains its legacy Supabase repository and authentication flows during shared API development.

Use Flutter 3.44.7, an Android SDK and JDK 17. From this directory:

```sh
flutter pub get
flutter analyze
flutter test
flutter build apk --debug --dart-define=SUPABASE_URL=https://example.supabase.co --dart-define=SUPABASE_ANON_KEY=synthetic-ci-key
test -s build/app/outputs/flutter-apk/app-debug.apk
```

For an operational development run, copy `env.example.json` to ignored `env.json`, supply an approved development project's URL and publishable key, then run `./scripts/run.sh`. Database authorization depends on legacy RLS policies. Never put a service-role key in the app. Synthetic CI values are for build checks only.

The inherited release configuration uses debug signing. Production requires reviewed signing and distribution configuration. This import verifies a debug APK; iOS scaffolding is absent from the pinned source. See [toolchains](../../docs/operations/toolchains.md), [migration](../../docs/migration/ROADMAP.md), and [architecture](../../docs/architecture/README.md).

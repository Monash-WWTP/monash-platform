# CitizenFlood Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a cross-platform (Android / iOS / Huawei) mobile app where citizens report flood, rain, river-gauge, and water-level observations with a photo and auto-captured GPS, all aggregated as pins on a shared live map.

**Architecture:** A Flutter app talking directly to a hosted Supabase backend (Postgres database + Storage for photos + anonymous Auth). No custom server. Maps use OpenStreetMap tiles (no Google dependency, so it runs on Huawei). State is kept simple with `StatefulWidget` + `FutureBuilder` and a single injectable `ReportRepository` — no heavy state-management library, to stay beginner/AI-friendly.

**Tech Stack:** Flutter (Dart 3) · `supabase_flutter` · `flutter_map` + `latlong2` · `geolocator` · `image_picker` · `permission_handler` · `intl`

---

## File Structure

```
citizenflood/
├── pubspec.yaml                       # deps + app metadata
├── supabase/
│   └── schema.sql                     # tables, storage bucket, RLS policies (run in Supabase)
├── lib/
│   ├── main.dart                      # app entry, Supabase init, anonymous sign-in
│   ├── config/
│   │   └── env.dart                   # reads SUPABASE_URL / SUPABASE_ANON_KEY from --dart-define
│   ├── theme/
│   │   └── app_theme.dart             # colors, typography (clean/aesthetic)
│   ├── models/
│   │   └── report.dart                # Report model + ReportCategory + Severity enums
│   ├── services/
│   │   ├── location_service.dart      # geolocator wrapper -> LatLng
│   │   └── report_repository.dart     # Supabase insert/upload/fetch
│   ├── widgets/
│   │   └── category_tile.dart         # reusable big category button
│   └── screens/
│       ├── home_shell.dart            # bottom nav: Report / Map / Me
│       ├── category_screen.dart       # pick what you saw (the "Report" tab root)
│       ├── report_form_screen.dart    # photo + auto-GPS + severity + note + submit
│       ├── map_screen.dart            # OSM map with pins + recent list
│       └── profile_screen.dart        # anonymous id + optional email sign-in
└── test/
    ├── models/report_test.dart        # serialization + enum parsing (TDD)
    └── widgets/category_tile_test.dart# widget smoke test
```

**Responsibility boundaries:**
- `models/report.dart` — pure data + (de)serialization. No Flutter, no Supabase imports. Fully unit-testable.
- `services/*` — all I/O (GPS, network). Screens never call Supabase directly; they go through `ReportRepository`.
- `screens/*` — UI only; one screen = one job.
- `config/env.dart` — the single place secrets enter the app (never hard-coded).

---

## Task 0: Prerequisites (one-time manual setup)

These are environment steps, not code. Check each off before Task 1.

- [ ] **Install Flutter SDK** (stable channel) and run `flutter doctor` — resolve any ❌ for Android toolchain. Building the **iOS** target additionally requires a **Mac with Xcode**; building **Huawei/Android** only needs the Android SDK.

```bash
flutter --version          # expect Flutter 3.x / Dart 3.x
flutter doctor             # Android toolchain must be ✓ (Xcode ✓ too, if building iOS)
```

- [ ] **Create a free Supabase account** at https://supabase.com and create a new project named `citizenflood`. From **Project Settings → API**, copy the **Project URL** and the **anon public key** — you'll need them in Task 3.
- [ ] **Create the three store developer accounts** (can happen in parallel with development; only needed at Task 14): Google Play ($25 once), Apple Developer Program ($99/yr), Huawei AppGallery (free).

---

## Task 1: Scaffold the Flutter project

**Files:**
- Create: `pubspec.yaml` (generated, then edited)
- Create: `lib/main.dart` (generated, replaced in Task 3)

- [ ] **Step 1: Generate the project in place**

The repo folder already exists with `docs/` and `.gitignore`. Generate Flutter into it:

```bash
cd /Users/jienweng/Documents/Monash/citizenflood
flutter create --org au.edu.monash --project-name citizenflood --platforms=android,ios .
```

- [ ] **Step 2: Add dependencies**

Run:

```bash
flutter pub add supabase_flutter flutter_map latlong2 geolocator image_picker permission_handler intl
```

Expected: `pubspec.yaml` now lists those under `dependencies:` and `flutter pub get` succeeds.

- [ ] **Step 3: Verify it runs**

Run (with an emulator or device connected):

```bash
flutter run
```

Expected: the default Flutter counter app launches. Stop it (`q`).

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: scaffold Flutter project with core dependencies"
```

---

## Task 2: Supabase schema (database, storage, security)

**Files:**
- Create: `supabase/schema.sql`

- [ ] **Step 1: Write the schema**

Create `supabase/schema.sql`:

```sql
-- Reports submitted by citizens.
create table if not exists public.reports (
  id           uuid primary key default gen_random_uuid(),
  category     text not null check (category in ('flood','rain','river_gauge','water_level')),
  severity     text not null check (severity in ('low','medium','high')),
  note         text,
  latitude     double precision not null,
  longitude    double precision not null,
  photo_path   text,                    -- path inside the report-photos storage bucket
  reporter_id  uuid default auth.uid(), -- anonymous or signed-in user id
  created_at   timestamptz not null default now()
);

-- Speed up "recent reports" and map queries.
create index if not exists reports_created_at_idx on public.reports (created_at desc);

-- Row Level Security: anyone (incl. anonymous) may read all reports and insert their own.
alter table public.reports enable row level security;

create policy "reports are public to read"
  on public.reports for select
  using (true);

create policy "anyone authenticated may insert"
  on public.reports for insert
  with check (auth.uid() is not null);

-- Storage bucket for photos (public read so the map can show them).
insert into storage.buckets (id, name, public)
  values ('report-photos', 'report-photos', true)
  on conflict (id) do nothing;

create policy "photos are public to read"
  on storage.objects for select
  using (bucket_id = 'report-photos');

create policy "authenticated may upload photos"
  on storage.objects for insert
  with check (bucket_id = 'report-photos' and auth.uid() is not null);
```

- [ ] **Step 2: Apply it in Supabase**

In the Supabase dashboard → **SQL Editor** → paste the contents of `supabase/schema.sql` → **Run**.
Expected: "Success. No rows returned." Then check **Table Editor** shows a `reports` table and **Storage** shows a `report-photos` bucket.

- [ ] **Step 3: Enable anonymous sign-ins**

Dashboard → **Authentication → Providers → Anonymous** → toggle **ON** → Save.
(This lets citizens submit without creating an account, while still satisfying the `auth.uid() is not null` policy.)

- [ ] **Step 4: Commit**

```bash
git add supabase/schema.sql
git commit -m "feat: add Supabase schema, storage bucket, and RLS policies"
```

---

## Task 3: Wire Supabase into the app

**Files:**
- Create: `lib/config/env.dart`
- Modify: `lib/main.dart`

- [ ] **Step 1: Create the env reader**

Create `lib/config/env.dart`:

```dart
/// Secrets are injected at build time via --dart-define so they never live in source.
class Env {
  static const supabaseUrl = String.fromEnvironment('SUPABASE_URL');
  static const supabaseAnonKey = String.fromEnvironment('SUPABASE_ANON_KEY');

  static void assertConfigured() {
    if (supabaseUrl.isEmpty || supabaseAnonKey.isEmpty) {
      throw StateError(
        'Missing SUPABASE_URL / SUPABASE_ANON_KEY. Pass them with --dart-define.',
      );
    }
  }
}
```

- [ ] **Step 2: Replace `lib/main.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'config/env.dart';
import 'theme/app_theme.dart';
import 'screens/home_shell.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  Env.assertConfigured();

  await Supabase.initialize(
    url: Env.supabaseUrl,
    anonKey: Env.supabaseAnonKey,
  );

  // Ensure every citizen has an identity (required by our insert policy).
  final auth = Supabase.instance.client.auth;
  if (auth.currentUser == null) {
    await auth.signInAnonymously();
  }

  runApp(const CitizenFloodApp());
}

class CitizenFloodApp extends StatelessWidget {
  const CitizenFloodApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'CitizenFlood',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      home: const HomeShell(),
    );
  }
}
```

> Note: `app_theme.dart` and `home_shell.dart` are created in Tasks 7 and 8. The app won't compile until those exist — that's expected; we commit this task's file and move on.

- [ ] **Step 3: Define the run command (record it in the README for the dev)**

Create/append `README.md`:

```markdown
## Running locally

    flutter run \
      --dart-define=SUPABASE_URL=https://YOUR_PROJECT.supabase.co \
      --dart-define=SUPABASE_ANON_KEY=YOUR_ANON_KEY
```

- [ ] **Step 4: Commit**

```bash
git add lib/config/env.dart lib/main.dart README.md
git commit -m "feat: initialize Supabase and anonymous auth on startup"
```

---

## Task 4: Report model + enums (TDD)

**Files:**
- Create: `lib/models/report.dart`
- Test: `test/models/report_test.dart`

- [ ] **Step 1: Write the failing test**

Create `test/models/report_test.dart`:

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/models/report.dart';

void main() {
  test('category maps to and from its wire value', () {
    expect(ReportCategory.riverGauge.wire, 'river_gauge');
    expect(ReportCategoryX.fromWire('river_gauge'), ReportCategory.riverGauge);
  });

  test('toInsertMap produces the columns Supabase expects', () {
    final report = Report(
      category: ReportCategory.flood,
      severity: Severity.high,
      note: 'water over footpath',
      latitude: -37.91,
      longitude: 145.13,
      photoPath: 'abc.jpg',
    );

    final map = report.toInsertMap();

    expect(map['category'], 'flood');
    expect(map['severity'], 'high');
    expect(map['note'], 'water over footpath');
    expect(map['latitude'], -37.91);
    expect(map['longitude'], 145.13);
    expect(map['photo_path'], 'abc.jpg');
    // id / reporter_id / created_at are set by the database, not the client.
    expect(map.containsKey('id'), isFalse);
  });

  test('fromRow parses a database row including timestamp', () {
    final report = Report.fromRow({
      'id': 'uuid-1',
      'category': 'rain',
      'severity': 'low',
      'note': null,
      'latitude': 1.0,
      'longitude': 2.0,
      'photo_path': null,
      'created_at': '2026-06-05T10:33:00.000Z',
    });

    expect(report.category, ReportCategory.rain);
    expect(report.severity, Severity.low);
    expect(report.note, isNull);
    expect(report.latitude, 1.0);
    expect(report.createdAt!.toUtc().hour, 10);
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/models/report_test.dart`
Expected: FAIL — `report.dart` / `Report` not found.

- [ ] **Step 3: Write the model**

Create `lib/models/report.dart`:

```dart
enum ReportCategory { flood, rain, riverGauge, waterLevel }

extension ReportCategoryX on ReportCategory {
  String get wire => switch (this) {
        ReportCategory.flood => 'flood',
        ReportCategory.rain => 'rain',
        ReportCategory.riverGauge => 'river_gauge',
        ReportCategory.waterLevel => 'water_level',
      };

  String get label => switch (this) {
        ReportCategory.flood => 'Flood area',
        ReportCategory.rain => 'Rain',
        ReportCategory.riverGauge => 'River gauge',
        ReportCategory.waterLevel => 'Water level',
      };

  String get emoji => switch (this) {
        ReportCategory.flood => '🌊',
        ReportCategory.rain => '🌧️',
        ReportCategory.riverGauge => '📏',
        ReportCategory.waterLevel => '💧',
      };

  static ReportCategory fromWire(String value) =>
      ReportCategory.values.firstWhere((c) => c.wire == value);
}

enum Severity { low, medium, high }

extension SeverityX on Severity {
  String get wire => name; // 'low' | 'medium' | 'high'
  String get label => switch (this) {
        Severity.low => 'Low',
        Severity.medium => 'Medium',
        Severity.high => 'High',
      };
  static Severity fromWire(String value) =>
      Severity.values.firstWhere((s) => s.name == value);
}

class Report {
  final String? id;
  final ReportCategory category;
  final Severity severity;
  final String? note;
  final double latitude;
  final double longitude;
  final String? photoPath;
  final DateTime? createdAt;

  Report({
    this.id,
    required this.category,
    required this.severity,
    this.note,
    required this.latitude,
    required this.longitude,
    this.photoPath,
    this.createdAt,
  });

  /// Columns the client supplies on insert. DB fills id/reporter_id/created_at.
  Map<String, dynamic> toInsertMap() => {
        'category': category.wire,
        'severity': severity.wire,
        'note': note,
        'latitude': latitude,
        'longitude': longitude,
        'photo_path': photoPath,
      };

  factory Report.fromRow(Map<String, dynamic> row) => Report(
        id: row['id'] as String?,
        category: ReportCategoryX.fromWire(row['category'] as String),
        severity: SeverityX.fromWire(row['severity'] as String),
        note: row['note'] as String?,
        latitude: (row['latitude'] as num).toDouble(),
        longitude: (row['longitude'] as num).toDouble(),
        photoPath: row['photo_path'] as String?,
        createdAt: row['created_at'] == null
            ? null
            : DateTime.parse(row['created_at'] as String),
      );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `flutter test test/models/report_test.dart`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add lib/models/report.dart test/models/report_test.dart
git commit -m "feat: add Report model with serialization (TDD)"
```

---

## Task 5: Location service

**Files:**
- Create: `lib/services/location_service.dart`

- [ ] **Step 1: Write the service**

Create `lib/services/location_service.dart`:

```dart
import 'package:geolocator/geolocator.dart';
import 'package:latlong2/latlong.dart';

/// Thrown when we cannot obtain a location (permission denied or GPS off).
class LocationUnavailable implements Exception {
  final String message;
  LocationUnavailable(this.message);
  @override
  String toString() => message;
}

class LocationService {
  /// Returns the device's current position, requesting permission if needed.
  Future<LatLng> current() async {
    if (!await Geolocator.isLocationServiceEnabled()) {
      throw LocationUnavailable('Location services are turned off.');
    }

    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.denied ||
        permission == LocationPermission.deniedForever) {
      throw LocationUnavailable('Location permission was denied.');
    }

    final pos = await Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(accuracy: LocationAccuracy.high),
    );
    return LatLng(pos.latitude, pos.longitude);
  }
}
```

- [ ] **Step 2: Verify it compiles**

Run: `flutter analyze lib/services/location_service.dart`
Expected: "No issues found!"

> Note: this is thin I/O glue over the platform GPS — it is verified by running the app (Task 10), not by a unit test, since mocking the geolocator plugin adds complexity without real value at pilot scope.

- [ ] **Step 3: Commit**

```bash
git add lib/services/location_service.dart
git commit -m "feat: add location service wrapping geolocator"
```

---

## Task 6: Report repository (Supabase I/O)

**Files:**
- Create: `lib/services/report_repository.dart`

- [ ] **Step 1: Write the repository**

Create `lib/services/report_repository.dart`:

```dart
import 'dart:typed_data';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../models/report.dart';

class ReportRepository {
  ReportRepository([SupabaseClient? client])
      : _client = client ?? Supabase.instance.client;

  final SupabaseClient _client;
  static const _bucket = 'report-photos';

  /// Uploads a photo's bytes and returns its storage path.
  Future<String> uploadPhoto(Uint8List bytes, String fileExtension) async {
    final userId = _client.auth.currentUser!.id;
    final path = '$userId/${DateTime.now().millisecondsSinceEpoch}.$fileExtension';
    await _client.storage.from(_bucket).uploadBinary(path, bytes);
    return path;
  }

  /// Public URL for a stored photo path (bucket is public-read).
  String photoUrl(String path) =>
      _client.storage.from(_bucket).getPublicUrl(path);

  /// Inserts a report row.
  Future<void> submit(Report report) async {
    await _client.from('reports').insert(report.toInsertMap());
  }

  /// Fetches the most recent reports (newest first) for the map + list.
  Future<List<Report>> recent({int limit = 200}) async {
    final rows = await _client
        .from('reports')
        .select()
        .order('created_at', ascending: false)
        .limit(limit);
    return (rows as List)
        .map((r) => Report.fromRow(r as Map<String, dynamic>))
        .toList();
  }
}
```

- [ ] **Step 2: Verify it compiles**

Run: `flutter analyze lib/services/report_repository.dart`
Expected: "No issues found!"

- [ ] **Step 3: Commit**

```bash
git add lib/services/report_repository.dart
git commit -m "feat: add ReportRepository for Supabase insert/upload/fetch"
```

---

## Task 7: App theme

**Files:**
- Create: `lib/theme/app_theme.dart`

- [ ] **Step 1: Write the theme**

Create `lib/theme/app_theme.dart`:

```dart
import 'package:flutter/material.dart';

class AppTheme {
  static const seed = Color(0xFF00A05A); // water-green brand color

  static ThemeData light() {
    final scheme = ColorScheme.fromSeed(seedColor: seed);
    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: const Color(0xFFF4F7FB),
      appBarTheme: const AppBarTheme(centerTitle: true, elevation: 0),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size.fromHeight(52),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
        ),
      ),
      cardTheme: CardThemeData(
        elevation: 1,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
    );
  }
}
```

- [ ] **Step 2: Verify it compiles**

Run: `flutter analyze lib/theme/app_theme.dart`
Expected: "No issues found!"

- [ ] **Step 3: Commit**

```bash
git add lib/theme/app_theme.dart
git commit -m "feat: add app theme (Material 3, water-green brand)"
```

---

## Task 8: Home shell with bottom navigation

> **Spec note (Welcome screen):** The design's "Welcome screen — start reporting immediately, anonymously" is delivered as its *intent* rather than a separate gate screen: anonymous sign-in happens silently at launch (Task 3) and the app lands directly on the Report tab, which opens with a friendly "What did you see?" heading. Optional sign-in lives on the Me tab (Task 12). This is the smoothest possible first-run and faithfully honors "start reporting immediately." If a branded splash is wanted later, add it via `flutter_native_splash` — out of scope for the pilot.

**Files:**
- Create: `lib/screens/home_shell.dart`
- Create stubs referenced here: `lib/screens/category_screen.dart`, `lib/screens/map_screen.dart`, `lib/screens/profile_screen.dart` (filled in later tasks)

- [ ] **Step 1: Create temporary stubs so the shell compiles**

Create `lib/screens/category_screen.dart`:

```dart
import 'package:flutter/material.dart';

class CategoryScreen extends StatelessWidget {
  const CategoryScreen({super.key});
  @override
  Widget build(BuildContext context) =>
      const Center(child: Text('Report (coming in Task 9)'));
}
```

Create `lib/screens/map_screen.dart`:

```dart
import 'package:flutter/material.dart';

class MapScreen extends StatelessWidget {
  const MapScreen({super.key});
  @override
  Widget build(BuildContext context) =>
      const Center(child: Text('Map (coming in Task 11)'));
}
```

Create `lib/screens/profile_screen.dart`:

```dart
import 'package:flutter/material.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});
  @override
  Widget build(BuildContext context) =>
      const Center(child: Text('Me (coming in Task 12)'));
}
```

- [ ] **Step 2: Write the shell**

Create `lib/screens/home_shell.dart`:

```dart
import 'package:flutter/material.dart';
import 'category_screen.dart';
import 'map_screen.dart';
import 'profile_screen.dart';

class HomeShell extends StatefulWidget {
  const HomeShell({super.key});
  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _index = 0;
  static const _titles = ['Report', 'Live map', 'Me'];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_titles[_index])),
      body: IndexedStack(
        index: _index,
        children: const [CategoryScreen(), MapScreen(), ProfileScreen()],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.add_circle_outline), label: 'Report'),
          NavigationDestination(icon: Icon(Icons.map_outlined), label: 'Map'),
          NavigationDestination(icon: Icon(Icons.person_outline), label: 'Me'),
        ],
      ),
    );
  }
}
```

- [ ] **Step 3: Run the app end-to-end for the first time**

Run (substitute your Supabase values):

```bash
flutter run \
  --dart-define=SUPABASE_URL=https://YOUR_PROJECT.supabase.co \
  --dart-define=SUPABASE_ANON_KEY=YOUR_ANON_KEY
```

Expected: app launches, shows the 3-tab bar, tabs switch between placeholder texts, no startup crash (anonymous sign-in succeeds).

- [ ] **Step 4: Commit**

```bash
git add lib/screens/
git commit -m "feat: add home shell with Report/Map/Me bottom navigation"
```

---

## Task 9: Category screen (the "Report" tab)

**Files:**
- Create: `lib/widgets/category_tile.dart`
- Test: `test/widgets/category_tile_test.dart`
- Modify: `lib/screens/category_screen.dart` (replace stub)

- [ ] **Step 1: Write the failing widget test**

Create `test/widgets/category_tile_test.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/models/report.dart';
import 'package:citizenflood/widgets/category_tile.dart';

void main() {
  testWidgets('CategoryTile shows label and fires onTap', (tester) async {
    var tapped = false;
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: CategoryTile(
          category: ReportCategory.flood,
          onTap: () => tapped = true,
        ),
      ),
    ));

    expect(find.text('Flood area'), findsOneWidget);
    await tester.tap(find.byType(CategoryTile));
    expect(tapped, isTrue);
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/widgets/category_tile_test.dart`
Expected: FAIL — `category_tile.dart` not found.

- [ ] **Step 3: Write the widget**

Create `lib/widgets/category_tile.dart`:

```dart
import 'package:flutter/material.dart';
import '../models/report.dart';

class CategoryTile extends StatelessWidget {
  const CategoryTile({super.key, required this.category, required this.onTap});

  final ReportCategory category;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(category.emoji, style: const TextStyle(fontSize: 36)),
              const SizedBox(height: 10),
              Text(category.label,
                  style: Theme.of(context).textTheme.titleMedium),
            ],
          ),
        ),
      ),
    );
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `flutter test test/widgets/category_tile_test.dart`
Expected: PASS.

- [ ] **Step 5: Replace the category screen stub**

Replace `lib/screens/category_screen.dart`:

```dart
import 'package:flutter/material.dart';
import '../models/report.dart';
import '../widgets/category_tile.dart';
import 'report_form_screen.dart';

class CategoryScreen extends StatelessWidget {
  const CategoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          const SizedBox(height: 8),
          Text('What did you see?',
              style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 16),
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            children: [
              for (final c in ReportCategory.values)
                CategoryTile(
                  category: c,
                  onTap: () => Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => ReportFormScreen(category: c),
                    ),
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }
}
```

> Note: `report_form_screen.dart` is created in Task 10. Compilation completes after that task; the test from this task already passes independently.

- [ ] **Step 6: Commit**

```bash
git add lib/widgets/category_tile.dart test/widgets/category_tile_test.dart lib/screens/category_screen.dart
git commit -m "feat: add category tiles and selection grid (TDD widget)"
```

---

## Task 10: Report form screen (photo + GPS + submit)

**Files:**
- Create: `lib/screens/report_form_screen.dart`

- [ ] **Step 1: Write the screen**

Create `lib/screens/report_form_screen.dart`:

```dart
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:latlong2/latlong.dart';

import '../models/report.dart';
import '../services/location_service.dart';
import '../services/report_repository.dart';

class ReportFormScreen extends StatefulWidget {
  const ReportFormScreen({super.key, required this.category});
  final ReportCategory category;

  @override
  State<ReportFormScreen> createState() => _ReportFormScreenState();
}

class _ReportFormScreenState extends State<ReportFormScreen> {
  final _location = LocationService();
  final _repo = ReportRepository();
  final _noteController = TextEditingController();

  Severity _severity = Severity.medium;
  XFile? _photo;
  LatLng? _position;
  String? _locationError;
  bool _submitting = false;

  @override
  void initState() {
    super.initState();
    _captureLocation();
  }

  Future<void> _captureLocation() async {
    try {
      final pos = await _location.current();
      setState(() {
        _position = pos;
        _locationError = null;
      });
    } catch (e) {
      setState(() => _locationError = e.toString());
    }
  }

  Future<void> _pickPhoto(ImageSource source) async {
    final picked = await ImagePicker().pickImage(source: source, imageQuality: 70);
    if (picked != null) setState(() => _photo = picked);
  }

  Future<void> _submit() async {
    if (_position == null) {
      _snack('Waiting for location — please enable GPS and try again.');
      return;
    }
    setState(() => _submitting = true);
    try {
      String? photoPath;
      if (_photo != null) {
        final bytes = await _photo!.readAsBytes();
        final ext = _photo!.name.split('.').last;
        photoPath = await _repo.uploadPhoto(bytes, ext);
      }
      await _repo.submit(Report(
        category: widget.category,
        severity: _severity,
        note: _noteController.text.trim().isEmpty ? null : _noteController.text.trim(),
        latitude: _position!.latitude,
        longitude: _position!.longitude,
        photoPath: photoPath,
      ));
      if (!mounted) return;
      _snack('Report submitted — thank you!');
      Navigator.of(context).pop();
    } catch (e) {
      _snack('Could not submit: $e');
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  void _snack(String msg) =>
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
          title: Text('${widget.category.emoji} ${widget.category.label}')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Photo
          if (_photo != null)
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Image.file(File(_photo!.path), height: 180, fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => const SizedBox()),
            ),
          Row(children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () => _pickPhoto(ImageSource.camera),
                icon: const Icon(Icons.photo_camera_outlined),
                label: const Text('Camera'),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () => _pickPhoto(ImageSource.gallery),
                icon: const Icon(Icons.image_outlined),
                label: const Text('Gallery'),
              ),
            ),
          ]),
          const SizedBox(height: 16),

          // Location status
          Card(
            color: _locationError == null
                ? const Color(0xFFEAFAF2)
                : const Color(0xFFFDECEA),
            child: ListTile(
              leading: Icon(_locationError == null
                  ? Icons.location_on
                  : Icons.location_off),
              title: Text(_locationError == null
                  ? (_position == null
                      ? 'Getting your location…'
                      : 'Location captured automatically')
                  : _locationError!),
              trailing: _locationError != null
                  ? TextButton(
                      onPressed: _captureLocation, child: const Text('Retry'))
                  : null,
            ),
          ),
          const SizedBox(height: 16),

          // Severity
          Text('Severity', style: Theme.of(context).textTheme.labelLarge),
          const SizedBox(height: 8),
          SegmentedButton<Severity>(
            segments: const [
              ButtonSegment(value: Severity.low, label: Text('Low')),
              ButtonSegment(value: Severity.medium, label: Text('Medium')),
              ButtonSegment(value: Severity.high, label: Text('High')),
            ],
            selected: {_severity},
            onSelectionChanged: (s) => setState(() => _severity = s.first),
          ),
          const SizedBox(height: 16),

          // Note
          TextField(
            controller: _noteController,
            maxLines: 3,
            decoration: const InputDecoration(
              labelText: 'Note (optional)',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 24),

          FilledButton(
            onPressed: _submitting ? null : _submit,
            child: _submitting
                ? const SizedBox(
                    height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
                : const Text('Submit report'),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _noteController.dispose();
    super.dispose();
  }
}
```

- [ ] **Step 2: Verify it compiles**

Run: `flutter analyze`
Expected: "No issues found!" (the whole project now compiles — category screen's import is satisfied).

- [ ] **Step 3: Manual end-to-end test**

Run the app, go to Report → tap **Flood area** → allow location → take/pick a photo → choose severity → Submit.
Expected: "Report submitted — thank you!" snackbar; in the Supabase **Table Editor** a new `reports` row appears, and **Storage → report-photos** holds the image.

- [ ] **Step 4: Commit**

```bash
git add lib/screens/report_form_screen.dart
git commit -m "feat: add report form with photo, auto-GPS, severity, and submit"
```

---

## Task 11: Map screen (OSM pins + recent list)

**Files:**
- Modify: `lib/screens/map_screen.dart` (replace stub)

- [ ] **Step 1: Write the map screen**

Replace `lib/screens/map_screen.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:intl/intl.dart';

import '../models/report.dart';
import '../services/report_repository.dart';

class MapScreen extends StatefulWidget {
  const MapScreen({super.key});
  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  final _repo = ReportRepository();
  late Future<List<Report>> _future = _repo.recent();

  Color _pinColor(ReportCategory c) => switch (c) {
        ReportCategory.flood => const Color(0xFFE44),
        ReportCategory.rain => const Color(0xFF39F),
        ReportCategory.riverGauge => const Color(0xFF0A5),
        ReportCategory.waterLevel => const Color(0xFFFA3),
      };

  void _refresh() => setState(() => _future = _repo.recent());

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<Report>>(
      future: _future,
      builder: (context, snap) {
        if (snap.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snap.hasError) {
          return Center(
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              const Text('Could not load reports.'),
              TextButton(onPressed: _refresh, child: const Text('Retry')),
            ]),
          );
        }
        final reports = snap.data ?? [];
        final center = reports.isNotEmpty
            ? LatLng(reports.first.latitude, reports.first.longitude)
            : const LatLng(-37.8136, 144.9631); // Melbourne fallback

        return Column(
          children: [
            Expanded(
              child: FlutterMap(
                options: MapOptions(initialCenter: center, initialZoom: 12),
                children: [
                  TileLayer(
                    urlTemplate:
                        'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                    userAgentPackageName: 'au.edu.monash.citizenflood',
                  ),
                  MarkerLayer(
                    markers: [
                      for (final r in reports)
                        Marker(
                          point: LatLng(r.latitude, r.longitude),
                          width: 36,
                          height: 36,
                          child: Icon(Icons.location_on,
                              color: _pinColor(r.category), size: 36),
                        ),
                    ],
                  ),
                ],
              ),
            ),
            SizedBox(
              height: 160,
              child: reports.isEmpty
                  ? const Center(child: Text('No reports yet — be the first!'))
                  : ListView(
                      children: [
                        for (final r in reports.take(20))
                          ListTile(
                            dense: true,
                            leading: Text(r.category.emoji,
                                style: const TextStyle(fontSize: 22)),
                            title: Text('${r.category.label} · ${r.severity.label}'),
                            subtitle: Text(r.createdAt == null
                                ? ''
                                : DateFormat('d MMM, h:mm a').format(r.createdAt!.toLocal())),
                          ),
                      ],
                    ),
            ),
          ],
        );
      },
    );
  }
}
```

- [ ] **Step 2: Verify it compiles**

Run: `flutter analyze`
Expected: "No issues found!"

- [ ] **Step 3: Manual end-to-end test**

Run the app. Submit a report (Task 10 flow), then open the **Map** tab.
Expected: the map shows OpenStreetMap tiles with a colored pin at your location, and your report appears in the list below with category, severity, and time.

- [ ] **Step 4: Commit**

```bash
git add lib/screens/map_screen.dart
git commit -m "feat: add OSM map with report pins and recent list"
```

---

## Task 12: Profile / "Me" screen

**Files:**
- Modify: `lib/screens/profile_screen.dart` (replace stub)

- [ ] **Step 1: Write the screen**

Replace `lib/screens/profile_screen.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final user = Supabase.instance.client.auth.currentUser;
    final isAnonymous = user?.isAnonymous ?? true;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const SizedBox(height: 8),
        const CircleAvatar(radius: 36, child: Icon(Icons.person, size: 36)),
        const SizedBox(height: 12),
        Center(
          child: Text(
            isAnonymous ? 'Reporting anonymously' : (user?.email ?? 'Signed in'),
            style: Theme.of(context).textTheme.titleMedium,
          ),
        ),
        const SizedBox(height: 24),
        Card(
          child: ListTile(
            leading: const Icon(Icons.info_outline),
            title: const Text('About CitizenFlood'),
            subtitle: const Text(
                'Report flooding, rain, and water levels in your area. '
                'Your reports help researchers and your community stay safe.'),
          ),
        ),
        if (isAnonymous)
          Card(
            child: ListTile(
              leading: const Icon(Icons.mail_outline),
              title: const Text('Sign in with email (optional)'),
              subtitle: const Text(
                  'Optional — lets you keep your reports if you change phones.'),
              onTap: () => _promptEmailSignIn(context),
            ),
          ),
      ],
    );
  }

  Future<void> _promptEmailSignIn(BuildContext context) async {
    final controller = TextEditingController();
    final email = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Sign in with email'),
        content: TextField(
          controller: controller,
          keyboardType: TextInputType.emailAddress,
          decoration: const InputDecoration(hintText: 'you@example.com'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          FilledButton(
              onPressed: () => Navigator.pop(ctx, controller.text.trim()),
              child: const Text('Send link')),
        ],
      ),
    );
    if (email == null || email.isEmpty) return;
    try {
      await Supabase.instance.client.auth.signInWithOtp(email: email);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Check your email for a sign-in link.')),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Could not send link: $e')),
        );
      }
    }
  }
}
```

- [ ] **Step 2: Verify it compiles**

Run: `flutter analyze`
Expected: "No issues found!"

- [ ] **Step 3: Commit**

```bash
git add lib/screens/profile_screen.dart
git commit -m "feat: add profile screen with optional email sign-in"
```

---

## Task 13: Platform permissions, app name & icon

**Files:**
- Modify: `android/app/src/main/AndroidManifest.xml`
- Modify: `ios/Runner/Info.plist`
- Modify: `pubspec.yaml` (app icon tooling)

- [ ] **Step 1: Add Android permissions**

In `android/app/src/main/AndroidManifest.xml`, add inside `<manifest>` (above `<application>`):

```xml
<uses-permission android:name="android.permission.INTERNET"/>
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION"/>
<uses-permission android:name="android.permission.CAMERA"/>
```

- [ ] **Step 2: Add iOS usage descriptions**

In `ios/Runner/Info.plist`, add inside the top-level `<dict>`:

```xml
<key>NSLocationWhenInUseUsageDescription</key>
<string>CitizenFlood uses your location to tag where flooding is happening.</string>
<key>NSCameraUsageDescription</key>
<string>CitizenFlood uses the camera to attach a photo to your report.</string>
<key>NSPhotoLibraryUsageDescription</key>
<string>CitizenFlood lets you attach a photo from your library to your report.</string>
```

- [ ] **Step 3: Set the display name**

- Android: in `AndroidManifest.xml`, set `<application android:label="CitizenFlood" ...>`.
- iOS: in `Info.plist`, set `<key>CFBundleDisplayName</key><string>CitizenFlood</string>`.

- [ ] **Step 4: Add an app icon**

Place a 1024×1024 PNG at `assets/icon/icon.png`, then:

```bash
flutter pub add --dev flutter_launcher_icons
```

Append to `pubspec.yaml`:

```yaml
flutter_launcher_icons:
  android: true
  ios: true
  image_path: "assets/icon/icon.png"
  min_sdk_android: 21
```

Run: `dart run flutter_launcher_icons`
Expected: launcher icons generated for Android and iOS.

- [ ] **Step 5: Verify permissions work on device**

Run the app on a real Android device; submitting a report should now prompt for location and camera permission and succeed.

- [ ] **Step 6: Commit**

```bash
git add android/ ios/ pubspec.yaml pubspec.lock assets/
git commit -m "chore: add platform permissions, display name, and app icon"
```

---

## Task 14: Build & publish to all three stores

This task produces release artifacts and submits them. It is mostly configuration; do it once the app works on real devices.

- [ ] **Step 1: Create a release signing key (Android — used by both Play and Huawei)**

```bash
keytool -genkey -v -keystore ~/citizenflood-release.jks \
  -keyalg RSA -keysize 2048 -validity 10000 -alias citizenflood
```

Create `android/key.properties` (already git-ignored):

```properties
storePassword=YOUR_KEYSTORE_PASSWORD
keyPassword=YOUR_KEY_PASSWORD
keyAlias=citizenflood
storeFile=/Users/YOU/citizenflood-release.jks
```

In `android/app/build.gradle`, above the `android {` block, load it:

```gradle
def keystoreProperties = new Properties()
def keystorePropertiesFile = rootProject.file('key.properties')
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(new FileInputStream(keystorePropertiesFile))
}
```

Then inside `android { ... }`, add the signing config and point `release` at it:

```gradle
signingConfigs {
    release {
        keyAlias keystoreProperties['keyAlias']
        keyPassword keystoreProperties['keyPassword']
        storeFile keystoreProperties['storeFile'] ? file(keystoreProperties['storeFile']) : null
        storePassword keystoreProperties['storePassword']
    }
}
buildTypes {
    release {
        signingConfig signingConfigs.release
    }
}
```

**Back up this keystore** — losing it means you cannot update the app on Google Play.

- [ ] **Step 2: Build the Android App Bundle (Google Play)**

```bash
flutter build appbundle \
  --dart-define=SUPABASE_URL=https://YOUR_PROJECT.supabase.co \
  --dart-define=SUPABASE_ANON_KEY=YOUR_ANON_KEY
```

Output: `build/app/outputs/bundle/release/app-release.aab`. Upload it in the **Google Play Console** → create app → Internal testing track first.

- [ ] **Step 3: Build the APK (Huawei AppGallery)**

```bash
flutter build apk --release \
  --dart-define=SUPABASE_URL=https://YOUR_PROJECT.supabase.co \
  --dart-define=SUPABASE_ANON_KEY=YOUR_ANON_KEY
```

Output: `build/app/outputs/flutter-apk/app-release.apk`. In **AppGallery Connect** → create app → upload the APK. Because the app uses **OpenStreetMap + direct GPS (no Google services)**, no HMS integration is required — it runs as-is on Huawei devices.

- [ ] **Step 4: Build & submit iOS (App Store) — requires a Mac**

```bash
flutter build ipa \
  --dart-define=SUPABASE_URL=https://YOUR_PROJECT.supabase.co \
  --dart-define=SUPABASE_ANON_KEY=YOUR_ANON_KEY
```

Open `build/ios/archive/Runner.xcarchive` in Xcode → Distribute App → App Store Connect. Then in **App Store Connect**, complete the listing and submit for review. (No Mac? Use a cloud build service such as Codemagic with the same `flutter build ipa` command.)

- [ ] **Step 5: Store listing assets (all three)**

Prepare once, reuse: app name "CitizenFlood", short description, screenshots (capture from a running device for several screen sizes), a privacy-policy URL (required by all three stores — state that location + photos are collected for flood reporting), and choose the appropriate content rating.

- [ ] **Step 6: Tag the release**

```bash
git tag v0.1.0-pilot
git commit --allow-empty -m "release: v0.1.0 pilot submitted to Play, App Store, AppGallery"
```

---

## Verification checklist (whole app)

- [ ] A new install can submit a report anonymously (no sign-up) with photo + auto-GPS.
- [ ] The submitted report appears as a row in Supabase and as a pin + list entry on the Map tab.
- [ ] The app launches and the map renders on a **Huawei device** (no Google services) — OSM tiles and pins visible.
- [ ] Location and camera permission prompts appear with the correct wording on Android and iOS.
- [ ] `flutter analyze` is clean and `flutter test` passes (model + widget tests).
- [ ] Release builds produced for AAB (Play), APK (Huawei), and IPA (App Store).
```

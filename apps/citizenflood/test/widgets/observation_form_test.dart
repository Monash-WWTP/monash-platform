import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/screens/observation_form_screen.dart';
import 'package:citizenflood/services/observation_repository.dart';
import 'package:citizenflood/services/account_session.dart';
import 'package:citizenflood/models/observation.dart';
import 'package:citizenflood/models/report.dart';
import 'package:citizenflood/maps/map_selection.dart';

class Picker extends ImagePicker {
  @override
  Future<XFile?> pickImage({
    required ImageSource source,
    double? maxWidth,
    double? maxHeight,
    int? imageQuality,
    CameraDevice preferredCameraDevice = CameraDevice.rear,
    bool requestFullMetadata = true,
  }) async => XFile('assets/icon/icon.png');
}

class Repo extends ObservationRepository {
  bool available = true;
  @override
  Future<bool> supportsRevision(int revision) async => available;
  bool fail = true;
  final writes = <Map<String, dynamic>>[];
  final keys = <String>[];
  @override
  Future<bool> supported() async => available;
  @override
  Future<void> submit(ObservationDraft draft, String key) async {
    writes.add(draft.payload);
    keys.add(key);
    if (fail) throw StateError('Uncertain write');
  }
}

class Session extends AccountSession {
  int revision = 0;
  @override
  int get generation => revision;
  void change() {
    revision++;
    notifyListeners();
  }

  @override
  bool get signedIn => true;
}

void main() {
  const location = SelectedLocation(
    latitude: 3,
    longitude: 101,
    source: LocationSource.selected,
  );
  testWidgets(
    'picker provenance changes on replacement and clears on removal',
    (t) async {
      await t.pumpWidget(
        MaterialApp(
          home: ObservationFormScreen(
            kind: 'rain_occurrence',
            location: location,
            repository: Repo(),
            session: Session(),
            picker: Picker(),
          ),
        ),
      );
      await t.pumpAndSettle();
      await t.tap(find.text('Unsure'));
      await t.tap(find.text('Photo and note'));
      await t.pumpAndSettle();
      for (final source in ['Gallery', 'Camera']) {
        await t.scrollUntilVisible(
          find.text(source),
          200,
          scrollable: find
              .descendant(
                of: find.byType(ListView),
                matching: find.byType(Scrollable),
              )
              .first,
        );
        await t.tap(find.text(source));
        await t.pumpAndSettle();
        await t.scrollUntilVisible(
          find.text('Review report'),
          200,
          scrollable: find
              .descendant(
                of: find.byType(ListView),
                matching: find.byType(Scrollable),
              )
              .first,
        );
        await t.tap(find.text('Review report'));
        await t.pumpAndSettle();
        expect(
          find.text('Photo source: ${source.toLowerCase()}'),
          findsOneWidget,
        );
        await t.scrollUntilVisible(
          find.text('Edit report'),
          200,
          scrollable: find
              .descendant(
                of: find.byType(ListView),
                matching: find.byType(Scrollable),
              )
              .first,
        );
        await t.tap(find.text('Edit report'));
        await t.pumpAndSettle();
      }
      await t.scrollUntilVisible(
        find.text('Remove photo'),
        -200,
        scrollable: find
            .descendant(
              of: find.byType(ListView),
              matching: find.byType(Scrollable),
            )
            .first,
      );
      await t.tap(find.text('Remove photo'));
      await t.pumpAndSettle();
      await t.scrollUntilVisible(
        find.text('Review report'),
        200,
        scrollable: find
            .descendant(
              of: find.byType(ListView),
              matching: find.byType(Scrollable),
            )
            .first,
      );
      await t.tap(find.text('Review report'));
      await t.pumpAndSettle();
      expect(find.textContaining('Photo source:'), findsNothing);
    },
  );
  testWidgets(
    'flood update reviews optional movement and comparison, clearing them for unsure',
    (t) async {
      final repo = Repo()..fail = false;
      final original = Report(
        id: 'previous',
        category: ReportCategory.waterLevel,
        observation: CitizenObservation({
          'kind': 'flooding',
          'method': 'visual',
          'response': 'present',
          'surfaces': ['road'],
        }),
        latitude: 3,
        longitude: 101,
        observedAt: DateTime.utc(2026, 10, 1),
      );
      await t.pumpWidget(
        MaterialApp(
          home: ObservationFormScreen(
            kind: 'flooding',
            location: location,
            previous: original,
            repository: repo,
            session: Session(),
          ),
        ),
      );
      await t.pumpAndSettle();
      await t.tap(find.text('Observed').first);
      await t.pumpAndSettle();
      await t.tap(find.text('Road'));
      await t.tap(find.text('Flowing'));
      await t.ensureVisible(find.text('Higher'));
      await t.tap(find.text('Higher'));
      await t.scrollUntilVisible(find.text('Review report'), 250);
      await t.tap(find.text('Review report'));
      await t.pumpAndSettle();
      expect(find.text('Movement: flowing'), findsOneWidget);
      expect(find.text('Change: higher'), findsOneWidget);
      await t.ensureVisible(find.text('Edit report'));
      await t.tap(find.text('Edit report'));
      await t.pumpAndSettle();
      await t.scrollUntilVisible(
        find.widgetWithText(RadioListTile<String>, 'Unsure'),
        -250,
      );
      await t.tap(find.widgetWithText(RadioListTile<String>, 'Unsure'));
      await t.pumpAndSettle();
      await t.scrollUntilVisible(find.text('Review report'), 250);
      await t.tap(find.text('Review report'));
      await t.pumpAndSettle();
      await t.ensureVisible(find.text('Submit report'));
      await t.tap(find.text('Submit report'));
      await t.pumpAndSettle();
      expect(repo.writes.single['protocol_revision'], 2);
      expect(repo.writes.single['previous_observation_id'], 'previous');
      expect(repo.writes.single['level_change'], isNull);
      expect(repo.writes.single['observation']['movement'], isNull);
      expect(repo.writes.single['location_accuracy_m'], isNull);
    },
  );
  testWidgets(
    'unknown is explicit, review is read only and uncertain retry keeps payload/key',
    (t) async {
      final repo = Repo();
      await t.pumpWidget(
        MaterialApp(
          home: ObservationFormScreen(
            kind: 'rain_occurrence',
            location: location,
            repository: repo,
            session: Session(),
          ),
        ),
      );
      await t.pumpAndSettle();
      await t.tap(find.text('Review report'));
      await t.pumpAndSettle();
      expect(find.text('Choose what you observed, or Unsure.'), findsOneWidget);
      expect(repo.writes, isEmpty);
      await t.tap(find.text('Unsure'));
      await t.tap(find.text('Review report'));
      await t.pumpAndSettle();
      expect(find.text('Unknown'), findsOneWidget);
      expect(repo.writes, isEmpty);
      await t.tap(find.text('Submit report'));
      await t.pumpAndSettle();
      expect(find.text('Uncertain write'), findsOneWidget);
      repo.fail = false;
      await t.tap(find.text('Submit report'));
      await t.pumpAndSettle();
      expect(repo.keys[0], repo.keys[1]);
      expect(repo.writes[0], repo.writes[1]);
      expect(repo.writes[0]['observation']['response'], 'unknown');
      expect(find.text('Pending review'), findsOneWidget);
    },
  );

  testWidgets(
    'returning to unchanged form after uncertain write keeps frozen time and key',
    (t) async {
      final repo = Repo();
      await t.pumpWidget(
        MaterialApp(
          home: ObservationFormScreen(
            kind: 'rain_occurrence',
            location: location,
            repository: repo,
            session: Session(),
          ),
        ),
      );
      await t.pumpAndSettle();
      await t.tap(find.text('Unsure'));
      await t.tap(find.text('Review report'));
      await t.pumpAndSettle();
      await t.tap(find.text('Submit report'));
      await t.pumpAndSettle();
      await t.tap(find.text('Edit report'));
      await t.pumpAndSettle();
      await t.pump(const Duration(seconds: 2));
      await t.tap(find.text('Review report'));
      await t.pumpAndSettle();
      repo.fail = false;
      await t.tap(find.text('Submit report'));
      await t.pumpAndSettle();
      expect(repo.keys[0], repo.keys[1]);
      expect(repo.writes[0], repo.writes[1]);
    },
  );
  testWidgets(
    'account change invalidates pending draft instead of resubmitting as another user',
    (t) async {
      final repo = Repo();
      final session = Session();
      await t.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Builder(
              builder: (c) => TextButton(
                onPressed: () => Navigator.push(
                  c,
                  MaterialPageRoute(
                    builder: (_) => ObservationFormScreen(
                      kind: 'rain_occurrence',
                      location: location,
                      repository: repo,
                      session: session,
                    ),
                  ),
                ),
                child: const Text('Start'),
              ),
            ),
          ),
        ),
      );
      await t.tap(find.text('Start'));
      await t.pumpAndSettle();
      await t.tap(find.text('Unsure'));
      await t.tap(find.text('Review report'));
      await t.pumpAndSettle();
      await t.tap(find.text('Submit report'));
      await t.pumpAndSettle();
      session.change();
      await t.pumpAndSettle();
      expect(find.text('Submit report'), findsNothing);
      expect(find.text('Start'), findsOneWidget);
      expect(repo.writes.length, 1);
    },
  );
  testWidgets('unsupported backend does not expose new submission form', (
    t,
  ) async {
    final repo = Repo()..available = false;
    await t.pumpWidget(
      MaterialApp(
        home: ObservationFormScreen(
          kind: 'flooding',
          location: location,
          repository: repo,
          session: Session(),
        ),
      ),
    );
    await t.pumpAndSettle();
    expect(find.text('Review report'), findsNothing);
    expect(find.text('Retry'), findsOneWidget);
  });
}

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/screens/observation_form_screen.dart';
import 'package:citizenflood/services/observation_repository.dart';
import 'package:citizenflood/services/account_session.dart';
import 'package:citizenflood/models/observation.dart';
import 'package:citizenflood/maps/map_selection.dart';

class Repo extends ObservationRepository {
  bool available = true;
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

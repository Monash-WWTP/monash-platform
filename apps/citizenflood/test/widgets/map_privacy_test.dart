import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/models/report.dart';
import 'package:citizenflood/services/account_session.dart';
import 'package:citizenflood/services/report_repository.dart';
import 'package:citizenflood/screens/map_screen.dart';

class Session extends AccountSession {
  int revision = 0;
  @override
  int get generation => revision;
  void change() {
    revision++;
    notifyListeners();
  }
}

class Repository extends ReportRepository {
  final reads = <Completer<List<Report>>>[];
  final photo = Completer<Uint8List>();
  @override
  Future<Uint8List> photoBytes(String mediaId) => photo.future;
  @override
  Future<List<Report>> recent({int limit = 200}) {
    final read = Completer<List<Report>>();
    reads.add(read);
    return read.future;
  }
}

Report privateReport(String owner, {String? photoPath}) => Report(
  id: owner,
  category: ReportCategory.rainfall,
  readingValue: 12,
  latitude: 3.123456,
  longitude: 101.123456,
  note: '$owner private note',
  photoPath: photoPath,
);
void main() {
  testWidgets(
    'logout clears owner markers and dismisses open private details',
    (tester) async {
      final session = Session();
      final repo = Repository();
      await tester.pumpWidget(
        MaterialApp(
          home: MapScreen(session: session, repository: repo),
        ),
      );
      repo.reads.single.complete([privateReport('A')]);
      await tester.pump();
      await tester.tap(find.byTooltip('Rainfall'));
      await tester.pumpAndSettle();
      expect(find.text('A private note'), findsOneWidget);
      session.change();
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 400));
      expect(find.text('A private note'), findsNothing);
      expect(find.byTooltip('Rainfall'), findsNothing);
    },
  );
  testWidgets('late owner A read is discarded after logout and B sign in', (
    tester,
  ) async {
    final session = Session();
    final repo = Repository();
    await tester.pumpWidget(
      MaterialApp(
        home: MapScreen(session: session, repository: repo),
      ),
    );
    session.change();
    await tester.pump();
    session.change();
    await tester.pump();
    repo.reads.first.complete([privateReport('A')]);
    await tester.pump();
    expect(find.byTooltip('Rainfall'), findsNothing);
    expect(repo.reads.length, 3);
    repo.reads.last.complete([privateReport('B')]);
    await tester.pump();
    repo.reads[1].complete([]);
    await tester.pump();
    expect(find.text('1 observations available'), findsOneWidget);
    await tester.tap(find.byTooltip('Rainfall'));
    await tester.pumpAndSettle();
    expect(find.text('B private note'), findsOneWidget);
    expect(find.text('A private note'), findsNothing);
  });
  testWidgets(
    'late private photo completion cannot restore a dismissed detail',
    (tester) async {
      final session = Session();
      final repo = Repository();
      await tester.pumpWidget(
        MaterialApp(
          home: MapScreen(session: session, repository: repo),
        ),
      );
      repo.reads.single.complete([privateReport('A', photoPath: 'A-photo')]);
      await tester.pump();
      await tester.tap(find.byTooltip('Rainfall'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 400));
      expect(find.text('A private note'), findsOneWidget);
      session.change();
      await tester.pump();
      repo.photo.complete(Uint8List.fromList([1, 2, 3]));
      await tester.pump();
      expect(find.text('A private note'), findsNothing);
      expect(find.byType(Image), findsNothing);
      repo.reads.last.complete([]);
      await tester.pump();
    },
  );
  testWidgets(
    'logout resets the map camera instead of retaining a private exact location',
    (tester) async {
      final session = Session();
      final repo = Repository();
      await tester.pumpWidget(
        MaterialApp(
          home: MapScreen(session: session, repository: repo),
        ),
      );
      repo.reads.single.complete([privateReport('A')]);
      await tester.pump();
      expect(
        tester
            .widget<FlutterMap>(find.byType(FlutterMap))
            .mapController!
            .camera
            .center
            .latitude,
        3.123456,
      );
      session.change();
      await tester.pump();
      repo.reads.last.complete([]);
      await tester.pump();
      expect(
        tester
            .widget<FlutterMap>(find.byType(FlutterMap))
            .mapController!
            .camera
            .center
            .latitude,
        3.1390,
      );
    },
  );
}

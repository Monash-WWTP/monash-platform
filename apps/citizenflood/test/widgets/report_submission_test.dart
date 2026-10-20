import 'dart:async';
import 'dart:typed_data';
import 'package:image_picker/image_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:latlong2/latlong.dart';
import 'package:citizenflood/models/report.dart';
import 'package:citizenflood/services/account_session.dart';
import 'package:citizenflood/services/location_service.dart';
import 'package:citizenflood/services/report_repository.dart';
import 'package:citizenflood/screens/report_form_screen.dart';

class Picker extends ImagePicker {
  @override
  Future<XFile?> pickImage({
    required ImageSource source,
    double? maxWidth,
    double? maxHeight,
    int? imageQuality,
    CameraDevice preferredCameraDevice = CameraDevice.rear,
    bool requestFullMetadata = true,
  }) async =>
      XFile.fromData(Uint8List.fromList([1, 2, 3]), name: 'capture.png');
}

class Session extends AccountSession {
  @override
  bool get signedIn => true;
}

class DelayedSession extends AccountSession {
  final authorization = Completer<void>();
  bool ready = false;
  @override
  bool get signedIn => ready;
  @override
  Future<void> signIn() async {
    await authorization.future;
    ready = true;
  }
}

class Location extends LocationService {
  @override
  Future<CapturedLocation> current() async =>
      const CapturedLocation(coordinates: LatLng(3, 101), accuracyM: 4);
}

class Repository extends ReportRepository {
  int uploadCalls = 0;
  final upload = Completer<String>();
  @override
  Future<String> uploadPhoto(Uint8List bytes, String fileExtension) {
    uploadCalls++;
    return upload.future;
  }

  final reports = <Report>[];
  final keys = <String?>[];
  final requests = <Completer<void>>[];
  @override
  Future<void> submit(Report report, {String? idempotencyKey}) {
    reports.add(report);
    keys.add(idempotencyKey);
    final request = Completer<void>();
    requests.add(request);
    return request.future;
  }
}

void main() {
  testWidgets(
    'in-flight report locks every editor and uncertain retry keeps payload and key',
    (tester) async {
      final repo = Repository();
      await tester.pumpWidget(
        MaterialApp(
          home: ReportFormScreen(
            category: ReportCategory.wastewater,
            session: Session(),
            location: Location(),
            repository: repo,
          ),
        ),
      );
      await tester.pump();
      await tester.tap(find.text('Photo and note'));
      await tester.pumpAndSettle();
      final note = find.byWidgetPredicate(
        (w) => w is TextField && w.maxLines == 3,
      );
      await tester.ensureVisible(note);
      await tester.enterText(note, 'original');
      final submit = find.text('Submit reading');
      await tester.ensureVisible(submit);
      await tester.tap(submit);
      await tester.pump();
      expect(tester.widget<TextField>(note).enabled, isFalse);
      expect(
        tester
            .widget<SegmentedButton<Condition>>(
              find.byType(SegmentedButton<Condition>),
            )
            .onSelectionChanged,
        isNull,
      );
      for (final button in tester.widgetList<OutlinedButton>(
        find.byType(OutlinedButton),
      )) {
        expect(button.onPressed, isNull);
      }
      repo.requests.first.completeError(TimeoutException('response lost'));
      await tester.pump();
      tester
          .state<ScaffoldMessengerState>(find.byType(ScaffoldMessenger))
          .removeCurrentSnackBar();
      await tester.pumpAndSettle();
      await tester.ensureVisible(submit);
      await tester.tap(submit);
      await tester.pump();
      expect(repo.reports.length, 2);
      expect(identical(repo.reports[0], repo.reports[1]), isTrue);
      expect(repo.keys[1], repo.keys[0]);
      repo.requests.last.completeError(TimeoutException('response lost'));
      await tester.pump();
      tester
          .state<ScaffoldMessengerState>(find.byType(ScaffoldMessenger))
          .removeCurrentSnackBar();
      await tester.pumpAndSettle();
      await tester.ensureVisible(note);
      await tester.enterText(note, 'edited');
      await tester.ensureVisible(submit);
      await tester.tap(submit);
      await tester.pump();
      expect(repo.reports.last.note, 'edited');
      expect(repo.keys.last, isNot(repo.keys.first));
      repo.requests.last.completeError(TimeoutException('response lost'));
      await tester.pumpAndSettle();
    },
  );
  testWidgets('numeric and note snapshots are fixed before awaiting sign in', (
    tester,
  ) async {
    final session = DelayedSession();
    final repo = Repository();
    await tester.pumpWidget(
      MaterialApp(
        home: ReportFormScreen(
          category: ReportCategory.rainfall,
          session: session,
          location: Location(),
          repository: repo,
        ),
      ),
    );
    await tester.pump();
    final value = find.byWidgetPredicate(
      (w) => w is TextField && w.maxLines == 1,
    );
    await tester.enterText(value, '12');
    await tester.tap(find.text('Photo and note'));
    await tester.pumpAndSettle();
    final note = find.byWidgetPredicate(
      (w) => w is TextField && w.maxLines == 3,
    );
    await tester.ensureVisible(note);
    await tester.enterText(note, 'original');
    await tester.ensureVisible(find.text('Submit reading'));
    await tester.tap(find.text('Submit reading'));
    await tester.pump();
    expect(tester.widget<TextField>(value).enabled, isFalse);
    expect(tester.widget<TextField>(note).enabled, isFalse);
    // A non-user controller update must not alter the already captured payload either.
    tester.widget<TextField>(value).controller!.text = '99';
    tester.widget<TextField>(note).controller!.text = 'later';
    session.authorization.complete();
    await tester.pump();
    expect(repo.reports.single.readingValue, 12);
    expect(repo.reports.single.note, 'original');
    repo.requests.single.completeError(TimeoutException('response lost'));
    await tester.pumpAndSettle();
  });
  testWidgets(
    'photo upload preserves one snapshot and timeout retry reuses the uploaded photo',
    (tester) async {
      final repo = Repository();
      await tester.pumpWidget(
        MaterialApp(
          home: ReportFormScreen(
            category: ReportCategory.rainfall,
            session: Session(),
            location: Location(),
            repository: repo,
            imagePicker: Picker(),
          ),
        ),
      );
      await tester.pump();
      final value = find.byWidgetPredicate(
        (w) => w is TextField && w.maxLines == 1,
      );
      await tester.enterText(value, '12');
      final valueController = tester.widget<TextField>(value).controller!;
      await tester.tap(find.text('Photo and note'));
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.text('Gallery'));
      await tester.tap(find.text('Gallery'));
      await tester.pumpAndSettle();
      final note = find.byWidgetPredicate(
        (w) => w is TextField && w.maxLines == 3,
      );
      await tester.ensureVisible(note);
      await tester.enterText(note, 'original');
      final submit = find.text('Submit reading');
      await tester.ensureVisible(submit);
      await tester.tap(submit);
      await tester.pump();
      expect(repo.uploadCalls, 1);
      expect(tester.widget<TextField>(note).enabled, isFalse);
      valueController.text = '99';
      tester.widget<TextField>(note).controller!.text = 'later';
      repo.upload.complete('uploaded-photo');
      await tester.pump();
      expect(repo.reports.single.readingValue, 12);
      expect(repo.reports.single.note, 'original');
      expect(repo.reports.single.photoPath, 'uploaded-photo');
      repo.requests.single.completeError(TimeoutException('response lost'));
      await tester.pump();
      tester
          .state<ScaffoldMessengerState>(find.byType(ScaffoldMessenger))
          .removeCurrentSnackBar();
      await tester.pumpAndSettle();
      await tester.ensureVisible(submit);
      await tester.tap(submit);
      await tester.pump();
      expect(repo.uploadCalls, 1);
      expect(repo.reports.length, 2);
      expect(identical(repo.reports.first, repo.reports.last), isTrue);
      expect(repo.keys.first, repo.keys.last);
      repo.requests.last.completeError(TimeoutException('response lost'));
      await tester.pumpAndSettle();
    },
  );
  testWidgets('successful submission returns from the locked form', (
    tester,
  ) async {
    final repo = Repository();
    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) => Scaffold(
            body: TextButton(
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (_) => ReportFormScreen(
                    category: ReportCategory.wastewater,
                    session: Session(),
                    location: Location(),
                    repository: repo,
                  ),
                ),
              ),
              child: const Text('Open report'),
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Open report'));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('Submit reading'));
    await tester.tap(find.text('Submit reading'));
    await tester.pump();
    repo.requests.single.complete();
    await tester.pumpAndSettle();
    expect(find.byType(ReportFormScreen), findsNothing);
    expect(find.text('Open report'), findsOneWidget);
  });
}

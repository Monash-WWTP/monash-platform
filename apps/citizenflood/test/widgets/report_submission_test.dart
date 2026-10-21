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

Future<void> review(WidgetTester tester) async {
  await tester.scrollUntilVisible(
    find.text('Review report'),
    200,
    scrollable: find
        .descendant(
          of: find.byType(ListView),
          matching: find.byType(Scrollable),
        )
        .first,
  );
  await tester.tap(find.text('Review report'));
  await tester.pumpAndSettle();
}

Future<void> send(WidgetTester tester) async {
  await tester.scrollUntilVisible(
    find.text('Submit report'),
    200,
    scrollable: find
        .descendant(
          of: find.byType(ListView),
          matching: find.byType(Scrollable),
        )
        .first,
  );
  await tester.tap(find.text('Submit report'));
  await tester.pump();
}

Future<void> dismissError(WidgetTester tester) async {
  tester
      .state<ScaffoldMessengerState>(find.byType(ScaffoldMessenger))
      .removeCurrentSnackBar();
  await tester.pumpAndSettle();
}

Future<void> enterNote(WidgetTester tester, String text) async {
  await tester.tap(find.text('Photo and note'));
  await tester.pumpAndSettle();
  final note = find.byWidgetPredicate((w) => w is TextField && w.maxLines == 3);
  await tester.ensureVisible(note);
  await tester.enterText(note, text);
}

void main() {
  testWidgets('Android Back after success exits the submitted draft', (tester) async {
    final repo=Repository();
    await tester.pumpWidget(MaterialApp(home:Builder(builder:(context)=>Scaffold(body:TextButton(onPressed:()=>Navigator.push(context,MaterialPageRoute(builder:(_)=>ReportFormScreen(category:ReportCategory.wastewater,session:Session(),location:Location(),repository:repo))),child:const Text('Map home'))))));
    await tester.tap(find.text('Map home'));await tester.pumpAndSettle();await tester.tap(find.text('Normal'));await review(tester);await send(tester);repo.requests.single.complete();await tester.pumpAndSettle();
    expect(find.text('Pending review'),findsOneWidget);await tester.binding.handlePopRoute();await tester.pumpAndSettle();
    expect(find.text('Map home'),findsOneWidget);expect(find.byType(ReportFormScreen),findsNothing);
  });

  testWidgets('condition selection is explicit and review does not submit', (
    tester,
  ) async {
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
    expect(
      tester
          .widget<SegmentedButton<Condition>>(
            find.byType(SegmentedButton<Condition>),
          )
          .selected,
      isEmpty,
    );
    await tester.scrollUntilVisible(
      find.text('Review report'),
      200,
      scrollable: find
          .descendant(
            of: find.byType(ListView),
            matching: find.byType(Scrollable),
          )
          .first,
    );
    await tester.tap(find.text('Review report'));
    await tester.pump();
    expect(repo.reports, isEmpty);
    expect(find.text('Choose a plant condition.'), findsOneWidget);
    await dismissError(tester);
    await tester.ensureVisible(find.text('Normal'));
    await tester.tap(find.text('Normal'));
    await review(tester);
    expect(find.text('Review report'), findsOneWidget);
    expect(repo.reports, isEmpty);
    expect(find.text('Normal'), findsOneWidget);
  });
  testWidgets(
    'uncertain retry reuses snapshot and key; edit starts a new payload',
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
      await tester.tap(find.text('Normal'));
      await enterNote(tester, 'original');
      await review(tester);
      await send(tester);
      expect(
        tester
            .widget<FilledButton>(
              find.widgetWithText(FilledButton, 'Submitting…'),
            )
            .onPressed,
        isNull,
      );
      repo.requests.first.completeError(TimeoutException('response lost'));
      await dismissError(tester);
      await send(tester);
      expect(repo.reports.length, 2);
      expect(identical(repo.reports.first, repo.reports.last), isTrue);
      expect(repo.keys.first, repo.keys.last);
      repo.requests.last.completeError(TimeoutException('response lost'));
      await dismissError(tester);
      await tester.tap(find.text('Edit report'));
      await tester.pumpAndSettle();
      final note = find.byWidgetPredicate(
        (w) => w is TextField && w.maxLines == 3,
      );
      await tester.scrollUntilVisible(
        note,
        -200,
        scrollable: find
            .descendant(
              of: find.byType(ListView),
              matching: find.byType(Scrollable),
            )
            .first,
      );
      await tester.enterText(note, 'edited');
      await review(tester);
      await send(tester);
      expect(repo.reports.last.note, 'edited');
      expect(repo.keys.last, isNot(repo.keys.first));
      repo.requests.last.completeError(TimeoutException('response lost'));
      await dismissError(tester);
    },
  );
  testWidgets('reviewed values are fixed before waiting for sign in', (
    tester,
  ) async {
    final repo = Repository();
    final session = DelayedSession();
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
    final valueController = tester.widget<TextField>(value).controller!;
    await enterNote(tester, 'original');
    final note = find.byWidgetPredicate(
      (w) => w is TextField && w.maxLines == 3,
    );
    final noteController = tester.widget<TextField>(note).controller!;
    await review(tester);
    await send(tester);
    valueController.text = '99';
    noteController.text = 'later';
    session.authorization.complete();
    await tester.pump();
    expect(repo.reports.single.readingValue, 12);
    expect(repo.reports.single.note, 'original');
    repo.requests.single.completeError(TimeoutException('response lost'));
    await dismissError(tester);
  });
  testWidgets(
    'photo upload is reused after uncertain submission; success is pending review',
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
      await enterNote(tester, 'original');
      await tester.ensureVisible(find.text('Gallery'));
      await tester.tap(find.text('Gallery'));
      await tester.pumpAndSettle();
      await review(tester);
      await send(tester);
      expect(repo.uploadCalls, 1);
      repo.upload.complete('uploaded-photo');
      await tester.pump();
      expect(repo.reports.single.photoPath, 'uploaded-photo');
      repo.requests.single.completeError(TimeoutException('response lost'));
      await dismissError(tester);
      await send(tester);
      expect(repo.uploadCalls, 1);
      expect(repo.keys.first, repo.keys.last);
      repo.requests.last.complete();
      await tester.pumpAndSettle();
      expect(find.text('Pending review'), findsOneWidget);
      expect(find.text('Back to map'), findsOneWidget);
    },
  );
}

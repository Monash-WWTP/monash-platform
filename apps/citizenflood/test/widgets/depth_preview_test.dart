import 'package:flutter/material.dart';
import 'package:citizenflood/services/account_session.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/services/depth_preview.dart';
import 'package:citizenflood/screens/depth_preview_screen.dart';
import 'package:citizenflood/widgets/measurement_fields.dart';
import 'package:citizenflood/widgets/report_detail_sheet.dart';
import 'package:citizenflood/models/report.dart';
import 'package:citizenflood/models/observation.dart';

class PreviewSession extends AccountSession {
  int revision = 0;
  @override
  int get generation => revision;
  void change() {
    revision++;
    notifyListeners();
  }
}

void main() {
  setUp(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          DepthPreview.channel,
          (call) async => call.method == 'isSupported' ? true : null,
        );
  });
  tearDown(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(DepthPreview.channel, null);
  });
  final data = <String, dynamic>{
    'kind': 'water_reading',
    'reference_kind': 'depth',
    'unit': 'm',
    'value': 0.5,
    'reference_description': 'Road surface',
  };
  testWidgets(
    'draft action requires a described finite depth and preserves fields',
    (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: MeasurementFields(
                kind: 'water_reading',
                references: const [],
                onChanged: () {},
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      final action = find.widgetWithText(OutlinedButton, 'Preview depth');
      expect(tester.widget<OutlinedButton>(action).onPressed, isNull);
      await tester.enterText(find.byType(TextFormField).at(0), 'Road surface');
      await tester.enterText(find.byType(TextFormField).at(1), '0.5');
      await tester.pump();
      expect(tester.widget<OutlinedButton>(action).onPressed, isNotNull);
      await tester.ensureVisible(action);
      await tester.tap(action);
      await tester.pumpAndSettle();
      expect(find.text('Draft depth'), findsOneWidget);
      await tester.scrollUntilVisible(find.text('Return to report'), 200);
      await tester.tap(find.text('Return to report'));
      await tester.pumpAndSettle();
      expect(find.text('0.5'), findsOneWidget);
      expect(find.text('Road surface'), findsOneWidget);
    },
  );
  testWidgets('only owned structured depths expose the saved preview', (
    tester,
  ) async {
    for (final owner in [false, true]) {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ReportDetailSheet(
              ownerView: owner,
              report: Report(
                category: ReportCategory.waterLevel,
                latitude: 0,
                longitude: 0,
                isOwner: owner,
                observation: CitizenObservation(data),
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(
        find.text('Visualise reported depth'),
        owner ? findsOneWidget : findsNothing,
      );
    }
  });
  testWidgets('account change clears context and closes native camera', (
    tester,
  ) async {
    final session = PreviewSession();
    final calls = <String>[];
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(DepthPreview.channel, (call) async {
          calls.add(call.method);
          return call.method == 'isSupported' ? true : null;
        });
    addTearDown(
      () => TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(DepthPreview.channel, null),
    );
    await tester.pumpWidget(
      MaterialApp(
        home: DepthPreviewScreen(
          preview: DepthPreview.fromObservation(data)!,
          contextLabel: 'Private report',
          session: session,
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Private report'), findsOneWidget);
    await tester.scrollUntilVisible(find.text('Open AR preview'), 200);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Open AR preview'));
    await tester.pumpAndSettle();
    expect(calls, contains('open'));
    session.change();
    await tester.pumpAndSettle();
    expect(find.text('Private report'), findsNothing);
    expect(find.text('Reference: Road surface'), findsNothing);
    expect(calls, contains('close'));
  });
  testWidgets('native failure leaves a usable return to report', (
    tester,
  ) async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          DepthPreview.channel,
          (call) async => call.method == 'isSupported'
              ? true
              : throw PlatformException(
                  code: 'unavailable',
                  message: 'AR unavailable. Continue reporting normally.',
                ),
        );
    addTearDown(
      () => TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(DepthPreview.channel, null),
    );
    await tester.pumpWidget(
      MaterialApp(
        home: DepthPreviewScreen(
          preview: DepthPreview.fromObservation(data)!,
          contextLabel: 'Draft depth',
        ),
      ),
    );
    await tester.scrollUntilVisible(find.text('Open AR preview'), 200);
    await tester.ensureVisible(
      find.widgetWithText(OutlinedButton, 'Open AR preview'),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Open AR preview'));
    await tester.pumpAndSettle();
    expect(
      find.text('AR unavailable. Continue reporting normally.'),
      findsOneWidget,
    );
    await tester.scrollUntilVisible(find.text('Return to report'), 200);
    expect(find.text('Return to report'), findsOneWidget);
  });
  testWidgets('unsupported device hides AR and simulated actions', (
    tester,
  ) async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(DepthPreview.channel, (_) async => false);
    await tester.pumpWidget(
      MaterialApp(
        home: DepthPreviewScreen(
          preview: DepthPreview.fromObservation(data)!,
          contextLabel: 'Draft depth',
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Open AR preview'), findsNothing);
    expect(find.text('3D water preview'), findsNothing);
    expect(find.text('Camera water'), findsNothing);
    await tester.scrollUntilVisible(find.text('Return to report'), 200);
    expect(find.text('Return to report'), findsOneWidget);
  });
}

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/models/report.dart';
import 'package:citizenflood/models/observation.dart';
import 'package:citizenflood/widgets/report_detail_sheet.dart';

void main() {
  testWidgets('only owned flooding offers an update action', (t) async {
    var updates = 0;
    final report = Report(
      id: 'flood',
      category: ReportCategory.waterLevel,
      observation: CitizenObservation({
        'kind': 'flooding',
        'response': 'unknown',
      }),
      latitude: 3,
      longitude: 101,
      observedAt: DateTime.utc(2026, 10, 1),
    );
    for (final owner in [false, true]) {
      await t.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ReportDetailSheet(
              report: report,
              ownerView: owner,
              onUpdate: () => updates++,
            ),
          ),
        ),
      );
      await t.pumpAndSettle();
      expect(
        find.text('Report an update'),
        owner ? findsOneWidget : findsNothing,
      );
      if (owner) await t.tap(find.text('Report an update'));
    }
    expect(updates, 1);
  });
}

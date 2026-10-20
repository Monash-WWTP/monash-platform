import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/models/report.dart';
import 'package:citizenflood/widgets/report_menu.dart';

void main() {
  testWidgets(
    'floating report menu selects a category and dismisses on Back or outside',
    (t) async {
      ReportCategory? selected;
      await t.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Align(
              alignment: Alignment.bottomRight,
              child: ReportMenu(onSelected: (c) => selected = c),
            ),
          ),
        ),
      );
      expect(find.text('Rainfall'), findsNothing);
      await t.tap(find.byTooltip('New report'));
      await t.pumpAndSettle();
      for (final c in ReportCategory.values) {
        expect(
          find.text(
            c == ReportCategory.wastewater ? 'Plant condition' : c.label,
          ),
          findsOneWidget,
        );
      }
      await t.tap(find.text('Rainfall'));
      await t.pumpAndSettle();
      expect(selected, ReportCategory.rainfall);
      await t.tap(find.byTooltip('New report'));
      await t.pumpAndSettle();
      await t.binding.handlePopRoute();
      await t.pumpAndSettle();
      expect(find.text('Rainfall'), findsNothing);
      await t.tap(find.byTooltip('New report'));
      await t.pumpAndSettle();
      await t.tapAt(const Offset(10, 10));
      await t.pumpAndSettle();
      expect(find.text('Rainfall'), findsNothing);
    },
  );
  testWidgets('menu supports large text and reduced motion', (t) async {
    t.view.physicalSize = const Size(320, 700);
    t.view.devicePixelRatio = 1;
    addTearDown(t.view.resetPhysicalSize);
    addTearDown(t.view.resetDevicePixelRatio);
    await t.pumpWidget(
      MaterialApp(
        builder: (c, w) => MediaQuery(
          data: MediaQuery.of(
            c,
          ).copyWith(textScaler: TextScaler.linear(2), disableAnimations: true),
          child: w!,
        ),
        home: Scaffold(
          body: Align(
            alignment: Alignment.bottomRight,
            child: ReportMenu(onSelected: (_) {}),
          ),
        ),
      ),
    );
    await t.tap(find.byTooltip('New report'));
    await t.pumpAndSettle();
    expect(t.takeException(), isNull);
    expect(find.text('Water level'), findsOneWidget);
  });
}

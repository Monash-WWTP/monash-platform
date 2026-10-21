import 'dart:ui' show SemanticsAction;
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/models/report.dart';
import 'package:citizenflood/widgets/report_menu.dart';

void main() {
  testWidgets(
    'floating report menu selects a category and dismisses on Back or outside',
    (t) async {
      final semantics = t.ensureSemantics();
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
      expect(find.text('Rain'), findsNothing);
      await t.tap(find.byTooltip('New report'));
      await t.pumpAndSettle();
      for (final label in [
        'Flooding',
        'Rain',
        'Water appearance',
        'Add measurement',
      ]) {
        expect(find.text(label), findsOneWidget);
      }
      expect(find.byTooltip('Close report menu'), findsOneWidget);
      expect(
        t
            .getSemantics(find.bySemanticsLabel('Rain'))
            .getSemanticsData()
            .hasAction(SemanticsAction.tap),
        isTrue,
      );
      expect(find.byType(PopupMenuItem<ReportCategory>), findsNothing);
      await t.tap(find.text('Rain'));
      await t.pumpAndSettle();
      expect(selected, ReportCategory.rainfall);
      await t.tap(find.byTooltip('New report'));
      await t.pumpAndSettle();
      await t.binding.handlePopRoute();
      await t.pumpAndSettle();
      expect(find.text('Rain'), findsNothing);
      await t.tap(find.byTooltip('New report'));
      await t.pumpAndSettle();
      await t.tapAt(const Offset(10, 10));
      await t.pumpAndSettle();
      expect(find.text('Rain'), findsNothing);
      semantics.dispose();
    },
  );
  testWidgets('open bubbles remain reachable after rotation', (t) async {
    t.view.physicalSize = const Size(320, 700);
    t.view.devicePixelRatio = 1;
    addTearDown(t.view.resetPhysicalSize);
    addTearDown(t.view.resetDevicePixelRatio);
    await t.pumpWidget(
      MaterialApp(
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
    t.view.physicalSize = const Size(700, 320);
    await t.pumpAndSettle();
    final close = t.getRect(find.byTooltip('Close report menu'));
    expect(close.bottom, lessThanOrEqualTo(320));
    await t.tap(find.byTooltip('Close report menu'));
    await t.pumpAndSettle();
    expect(find.text('Rain'), findsNothing);
  });
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
    expect(find.text('Flooding'), findsOneWidget);
  });
}

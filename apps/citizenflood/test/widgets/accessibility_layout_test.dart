import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/screens/home_shell.dart';
import 'package:citizenflood/screens/report_form_screen.dart';
import 'package:citizenflood/models/report.dart';
import 'package:citizenflood/maps/map_selection.dart';

void main() {
  testWidgets('map header and legend fit a narrow screen with large text', (
    t,
  ) async {
    t.view.physicalSize = const Size(320, 700);
    t.view.devicePixelRatio = 1;
    addTearDown(t.view.resetPhysicalSize);
    addTearDown(t.view.resetDevicePixelRatio);
    await t.pumpWidget(
      MaterialApp(
        builder: (c, w) => MediaQuery(
          data: MediaQuery.of(c).copyWith(textScaler: TextScaler.linear(2)),
          child: w!,
        ),
        home: const HomeShell(),
      ),
    );
    await t.pump();
    expect(t.takeException(), isNull);
  });
  testWidgets(
    'large text form has no overflow and can change selected location',
    (t) async {
      t.view.physicalSize = const Size(320, 700);
      t.view.devicePixelRatio = 1;
      addTearDown(t.view.resetPhysicalSize);
      addTearDown(t.view.resetDevicePixelRatio);
      await t.pumpWidget(
        MaterialApp(
          builder: (c, w) => MediaQuery(
            data: MediaQuery.of(c).copyWith(textScaler: TextScaler.linear(2)),
            child: w!,
          ),
          home: const ReportFormScreen(
            category: ReportCategory.wastewater,
            selectedLocation: SelectedLocation(
              latitude: 3,
              longitude: 101,
              source: LocationSource.selected,
            ),
          ),
        ),
      );
      await t.pump();
      expect(t.takeException(), isNull);
      await t.scrollUntilVisible(find.text('Change location'),200,scrollable:find.descendant(of:find.byType(ListView),matching:find.byType(Scrollable)).first);
      expect(t.takeException(),isNull);
      expect(find.text('Change location'), findsOneWidget);
    },
  );
}

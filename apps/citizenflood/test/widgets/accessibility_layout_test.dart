import 'package:flutter/material.dart';
import 'package:citizenflood/screens/location_picker_screen.dart';
import 'package:citizenflood/maps/citizen_map.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/screens/home_shell.dart';
import 'package:citizenflood/screens/report_form_screen.dart';
import 'package:citizenflood/models/report.dart';
import 'package:citizenflood/maps/map_selection.dart';

void main() {
  testWidgets(
    'compact location panel keeps map visible on short large-text screen',
    (t) async {
      t.view.physicalSize = const Size(640, 360);
      t.view.devicePixelRatio = 1;
      addTearDown(t.view.resetPhysicalSize);
      addTearDown(t.view.resetDevicePixelRatio);
      await t.pumpWidget(
        MaterialApp(
          builder: (c, w) => MediaQuery(
            data: MediaQuery.of(c).copyWith(textScaler: TextScaler.linear(2)),
            child: w!,
          ),
          home: const LocationPickerScreen(),
        ),
      );
      await t.pump();
      expect(t.takeException(), isNull);
      expect(t.getSize(find.byType(CitizenMap)).height, greaterThan(0));
      expect(find.byTooltip('Use current location'), findsOneWidget);
    },
  );

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
      await t.scrollUntilVisible(
        find.text('Change location'),
        200,
        scrollable: find
            .descendant(
              of: find.byType(ListView),
              matching: find.byType(Scrollable),
            )
            .first,
      );
      expect(t.takeException(), isNull);
      expect(find.text('Change location'), findsOneWidget);
    },
  );
}

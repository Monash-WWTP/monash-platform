import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/screens/location_picker_screen.dart';
import 'package:citizenflood/maps/citizen_map.dart';
import 'package:citizenflood/maps/map_selection.dart';

void main() {
  testWidgets(
    'tap selects point without old GPS accuracy; details stay secondary',
    (t) async {
      SelectedLocation? chosen;
      await t.pumpWidget(
        MaterialApp(
          home: Builder(
            builder: (c) => Scaffold(
              body: TextButton(
                onPressed: () async {
                  chosen = await Navigator.push<SelectedLocation>(
                    c,
                    MaterialPageRoute(
                      builder: (_) => const LocationPickerScreen(
                        initialLocation: SelectedLocation(
                          latitude: 3,
                          longitude: 101,
                          source: LocationSource.current,
                          accuracyM: 8,
                        ),
                      ),
                    ),
                  );
                },
                child: const Text('Choose'),
              ),
            ),
          ),
        ),
      );
      await t.tap(find.text('Choose'));
      await t.pumpAndSettle();
      expect(find.text('±8 m'), findsOneWidget);
      expect(find.text('3.00000, 101.00000'), findsNothing);
      t.widget<CitizenMap>(find.byType(CitizenMap)).onPointSelected!(
        const SelectedLocation(
          latitude: 3.2,
          longitude: 101.2,
          source: LocationSource.selected,
        ),
      );
      await t.pumpAndSettle();
      expect(find.text('±8 m'), findsNothing);
      await t.tap(find.text('Use this location'));
      await t.pumpAndSettle();
      expect(chosen!.latitude, 3.2);
      expect(chosen!.longitude, 101.2);
      expect(chosen!.source, LocationSource.selected);
      expect(chosen!.accuracyM, isNull);
    },
  );
}

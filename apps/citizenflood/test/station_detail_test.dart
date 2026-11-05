import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/services/station_repository.dart';
import 'package:citizenflood/widgets/station_detail_sheet.dart';

class Samples extends StationRepository {
  Samples(this.row);
  final Map<String, dynamic>? row;
  @override
  Future<Map<String, dynamic>?> latestSample(String code) async => row;
}

void main() {
  const station = MonitoringStation(
    code: 'PTG248',
    name: 'PETALING-MAWAR',
    latitude: 3,
    longitude: 101,
  );
  testWidgets(
    'shows sample date and censoring without presenting historic data as live',
    (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: StationDetailSheet(
              station: station,
              repository: Samples({
                'sample_date': '2025-01-01',
                'bod': 2,
                'bod_bdl': true,
              }),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.textContaining('2025-01-01'), findsOneWidget);
      expect(find.textContaining('Below detection limit'), findsOneWidget);
      expect(find.textContaining('not live readings'), findsOneWidget);
    },
  );
  testWidgets('no history never displays demo simulation results', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: StationDetailSheet(station: station, repository: Samples(null)),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('No laboratory samples available.'), findsOneWidget);
    expect(find.textContaining('250'), findsNothing);
  });
}

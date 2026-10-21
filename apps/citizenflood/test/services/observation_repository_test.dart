import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:citizenflood/services/platform_api.dart';
import 'package:citizenflood/services/observation_repository.dart';

void main() {
  test('capability discovery recovers after a transient outage', () async {
    var calls = 0;
    final repo = ObservationRepository(
      PlatformApi(
        baseUrl: 'https://example.test',
        token: () async => null,
        client: MockClient((r) async {
          calls++;
          if (calls == 1) {
            return http.Response(
              '{"error":{"message":"temporary outage"}}',
              503,
            );
          }
          return http.Response(
            jsonEncode({
              'protocol_id': 'citizen-observation',
              'protocol_revision': 1,
              'types': [
                'flooding',
                'rain_occurrence',
                'water_appearance',
                'rainfall_accumulation',
                'water_reading',
                'temperature',
              ],
            }),
            200,
          );
        }),
      ),
    );
    await expectLater(repo.supported(), throwsStateError);
    expect(await repo.supported(), isTrue);
    expect(await repo.supportsRevision(2), isFalse);
    expect(calls, 2);
  });
}

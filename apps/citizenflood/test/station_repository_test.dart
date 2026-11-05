import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:citizenflood/services/platform_api.dart';
import 'package:citizenflood/services/station_repository.dart';

void main() {
  test(
    'loads all station pages and selects latest sample by date, not ID order',
    () async {
      final paths = <Uri>[];
      final api = PlatformApi(
        baseUrl: 'https://example.test',
        token: () async => null,
        client: MockClient((r) async {
          paths.add(r.url);
          if (r.url.path.endsWith('/stations')) {
            final offset = int.parse(r.url.queryParameters['offset']!);
            return http.Response(
              jsonEncode({
                'items': [
                  {
                    'code': offset == 0 ? 'NXP' : 'PTG248',
                    'name': 'Station',
                    'latitude': 3.0,
                    'longitude': 101.0,
                    'stp_type': 'SBR',
                  },
                ],
                'total': 2,
              }),
              200,
            );
          }
          return http.Response(
            jsonEncode({
              'items': [
                {'sample_date': '2025-11-01', 'bod': 8},
                {'sample_date': '2023-01-01', 'bod': 2},
              ],
              'total': 2,
            }),
            200,
          );
        }),
      );
      final repo = StationRepository(api: api);
      expect((await repo.stations()).map((s) => s.code), ['NXP', 'PTG248']);
      expect((await repo.latestSample('PTG248'))!['bod'], 8);
      expect(paths[1].queryParameters['offset'], '1');
      expect(paths.last.queryParameters['station_code'], 'PTG248');
    },
  );
  test(
    'empty sample history stays empty rather than using simulated values',
    () async {
      final repo = StationRepository(
        api: PlatformApi(
          baseUrl: 'https://example.test',
          token: () async => null,
          client: MockClient(
            (_) async => http.Response('{"items":[],"total":0}', 200),
          ),
        ),
      );
      expect(await repo.latestSample('NXP'), isNull);
    },
  );
  test(
    'incomplete pagination fails visibly rather than silently dropping stations',
    () async {
      final repo = StationRepository(
        api: PlatformApi(
          baseUrl: 'https://example.test',
          token: () async => null,
          client: MockClient(
            (_) async => http.Response('{"items":[],"total":21}', 200),
          ),
        ),
      );
      await expectLater(repo.stations(), throwsStateError);
    },
  );
}

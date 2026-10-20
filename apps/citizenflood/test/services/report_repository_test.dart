import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:citizenflood/services/platform_api.dart';
import 'package:citizenflood/services/report_repository.dart';

void main() {
  test('owner history uses only paginated owner endpoint', () async {
    final api = PlatformApi(
      baseUrl: 'https://example.test',
      token: () async => 'proof',
      client: MockClient((r) async {
        expect(r.url.path, '/api/v1/reports');
        expect(r.url.queryParameters, {'limit': '25', 'offset': '25'});
        return http.Response(
          '{"items":[],"total":40,"offset":25,"limit":25}',
          200,
        );
      }),
    );
    final page = await ReportRepository(api).own(offset: 25);
    expect(page.total, 40);
    expect(page.items, isEmpty);
  });
}

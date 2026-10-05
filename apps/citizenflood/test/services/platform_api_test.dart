import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:citizenflood/services/platform_api.dart';

void main() {
  test('sends scoped bearer proof to the API and propagates server errors', () async {
    final api = PlatformApi(baseUrl: 'https://api.example.test', token: () async => 'proof',
      client: MockClient((request) async {
        expect(request.url.path, '/api/v1/reports');
        expect(request.headers['Authorization'], 'Bearer proof');
        return http.Response('{"error":{"message":"Sign in required"}}', 401);
      }));
    expect(api.request('/api/v1/reports'), throwsStateError);
  });
}

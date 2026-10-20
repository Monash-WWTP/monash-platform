import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:citizenflood/screens/profile_screen.dart';
import 'package:citizenflood/services/account_session.dart';
import 'package:citizenflood/services/platform_api.dart';

class Session extends AccountSession {
  @override
  bool get signedIn => true;
}

void main() {
  testWidgets(
    'failed account request offers retry rather than endless loading',
    (t) async {
      int calls = 0;
      final api = PlatformApi(
        baseUrl: 'https://example.test',
        token: () async => 'proof',
        client: MockClient((r) async {
          calls++;
          return http.Response('{"error":{"message":"unavailable"}}', 503);
        }),
      );
      await t.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ProfileScreen(session: Session(), api: api),
          ),
        ),
      );
      await t.pumpAndSettle();
      expect(find.text('Account details unavailable.'), findsOneWidget);
      expect(find.text('Retry account details'), findsOneWidget);
      expect(calls, 1);
      await t.pump();
      expect(calls, 1);
    },
  );
}

import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:citizenflood/services/account_settings_launcher.dart';
import 'package:citizenflood/services/account_settings_repository.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:citizenflood/screens/profile_screen.dart';
import 'package:citizenflood/services/account_session.dart';
import 'package:citizenflood/services/platform_api.dart';

class Launcher extends AccountSettingsLauncher {
  String? action;
  @override
  Future<bool> open(AccountSettings settings, String action) async {
    this.action = action;
    return true;
  }
}

class Session extends AccountSession {
  int refreshes = 0;
  @override
  Future<void> refreshAccountProof() async {
    refreshes++;
  }

  @override
  bool get signedIn => true;
}

void main() {
  testWidgets(
    'account settings open correct action and refresh once on return at large text',
    (t) async {
      t.view.physicalSize = const Size(360, 800);
      t.view.devicePixelRatio = 1;
      addTearDown(t.view.resetPhysicalSize);
      addTearDown(t.view.resetDevicePixelRatio);
      final session = Session();
      final launcher = Launcher();
      int reads = 0;
      final api = PlatformApi(
        baseUrl: 'https://example.test',
        token: () async => 'proof',
        client: MockClient((r) async {
          if (r.url.path.endsWith('account-settings'))
            return http.Response(
              jsonEncode({
                'available': true,
                'origin': 'https://accounts.example.test',
                'actions': {
                  'profile':
                      'https://accounts.example.test/if/flow/monash-account-profile/',
                  'email':
                      'https://accounts.example.test/if/flow/monash-account-email/',
                },
              }),
              200,
            );
          reads++;
          return http.Response(
            jsonEncode({
              'email': 'qa@example.test',
              'display_name': reads > 1 ? 'Updated name' : 'Original name',
            }),
            200,
          );
        }),
      );
      await t.pumpWidget(
        MaterialApp(
          home: MediaQuery(
            data: const MediaQueryData(textScaler: TextScaler.linear(2)),
            child: Scaffold(
              body: ProfileScreen(
                session: session,
                api: api,
                settingsLauncher: launcher,
              ),
            ),
          ),
        ),
      );
      await t.pumpAndSettle();
      expect(find.text('Email & password'), findsOneWidget);
      await t.scrollUntilVisible(find.text('Security'), 150);
      expect(find.text('Security'), findsOneWidget);
      await t.ensureVisible(find.text('Profile'));
      await t.tap(find.text('Profile'));
      await t.pumpAndSettle();
      expect(launcher.action, 'profile');
      t.binding.handleAppLifecycleStateChanged(AppLifecycleState.paused);
      t.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
      await t.pumpAndSettle();
      expect(session.refreshes, 1);
      expect(find.text('Updated name'), findsOneWidget);
      t.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
      await t.pumpAndSettle();
      expect(session.refreshes, 1);
      expect(t.takeException(), isNull);
    },
  );
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

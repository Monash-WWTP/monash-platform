import 'dart:async';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:citizenflood/services/account_session.dart';

class DelayedStorage extends FlutterSecureStorage {
  final writing = Completer<void>();
  final release = Completer<void>();
  bool delayed = false;
  @override
  Future<void> write({
    required String key,
    required String? value,
    AppleOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    AppleOptions? mOptions,
    WindowsOptions? wOptions,
  }) async {
    if (!delayed) {
      delayed = true;
      writing.complete();
      await release.future;
    }
    await super.write(
      key: key,
      value: value,
      iOptions: iOptions,
      aOptions: aOptions,
      lOptions: lOptions,
      webOptions: webOptions,
      mOptions: mOptions,
      wOptions: wOptions,
    );
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const channel = MethodChannel('crossingthestreams.io/flutter_appauth');
  const storage = FlutterSecureStorage();
  late AccountSession session;
  late Completer<Map<String, dynamic>> refresh;
  Map<String, dynamic> credentials(String owner) => {
    'accessToken': '$owner-access',
    'refreshToken': '$owner-refresh',
    'idToken': '$owner-id',
    'accessTokenExpirationTime': DateTime.now()
        .add(const Duration(hours: 1))
        .millisecondsSinceEpoch,
  };
  setUp(() async {
    FlutterSecureStorage.setMockInitialValues({'refresh_token': 'A-refresh'});
    session = AccountSession();
    await session.initialize();
    refresh = Completer();
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
          if (call.method == 'token') return refresh.future;
          if (call.method == 'authorizeAndExchangeCode') {
            return credentials('B');
          }
          return <String, dynamic>{};
        });
  });
  tearDown(
    () => TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, null),
  );
  test('invalid grant clears the local identity on settings return', () async {
    final pending = session.refreshAccountProof();
    await Future<void>.delayed(Duration.zero);
    refresh.completeError(
      PlatformException(
        code: 'token_failed',
        details: {
          'error': 'invalid_grant',
          'legacy_error_details': 'native error',
        },
      ),
    );
    await expectLater(pending, throwsStateError);
    expect(session.signedIn, isFalse);
    expect(await storage.read(key: 'refresh_token'), isNull);
  });
  test('provider outage retains identity on settings return', () async {
    final pending = session.refreshAccountProof();
    await Future<void>.delayed(Duration.zero);
    refresh.completeError(
      PlatformException(
        code: 'token_failed',
        details: {'error': 'temporarily_unavailable'},
      ),
    );
    await expectLater(pending, throwsStateError);
    expect(session.signedIn, isTrue);
  });
  test('refresh finishing after logout cannot restore credentials', () async {
    final pending = session.token();
    await Future<void>.delayed(Duration.zero);
    await session.signOut();
    refresh.complete(credentials('A'));
    expect(await pending, isNull);
    expect(session.signedIn, isFalse);
    expect(await storage.read(key: 'refresh_token'), isNull);
  });
  test('old refresh cannot replace a newly signed in account', () async {
    final pending = session.token();
    await Future<void>.delayed(Duration.zero);
    await session.signOut();
    await session.signIn();
    refresh.complete(credentials('A'));
    expect(await pending, isNull);
    expect(await session.token(), 'B-access');
    expect(await storage.read(key: 'refresh_token'), 'B-refresh');
  });
  test('pending interactive sign in cannot undo logout', () async {
    final authorization = Completer<Map<String, dynamic>>();
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
          if (call.method == 'authorizeAndExchangeCode') {
            return authorization.future;
          }
          return <String, dynamic>{};
        });
    final pending = session.signIn();
    await Future<void>.delayed(Duration.zero);
    await session.signOut();
    authorization.complete(credentials('A'));
    await pending;
    expect(session.signedIn, isFalse);
    expect(await storage.read(key: 'refresh_token'), isNull);
  });
  test(
    'logout removes credentials even when a secure storage write is already running',
    () async {
      final delayed = DelayedStorage();
      session = AccountSession(storage: delayed);
      await session.initialize();
      final pending = session.token();
      refresh.complete(credentials('A'));
      await delayed.writing.future;
      final logout = session.signOut();
      expect(session.signedIn, isFalse);
      delayed.release.complete();
      expect(await pending, isNull);
      await logout;
      expect(await storage.read(key: 'refresh_token'), isNull);
      expect(await storage.read(key: 'id_token'), isNull);
    },
  );
  test('account B storage follows a write already running for A', () async {
    final delayed = DelayedStorage();
    session = AccountSession(storage: delayed);
    await session.initialize();
    final pending = session.token();
    refresh.complete(credentials('A'));
    await delayed.writing.future;
    final login = session.signIn();
    delayed.release.complete();
    await login;
    expect(await pending, isNull);
    expect(await session.token(), 'B-access');
    expect(await storage.read(key: 'refresh_token'), 'B-refresh');
    expect(await storage.read(key: 'id_token'), 'B-id');
  });
}

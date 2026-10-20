import 'package:flutter/foundation.dart';
import 'package:flutter_appauth/flutter_appauth.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../config/env.dart';

class AccountSession extends ChangeNotifier {
  AccountSession({FlutterSecureStorage? storage})
    : _storage = storage ?? const FlutterSecureStorage();
  static final instance = AccountSession();
  final FlutterAppAuth _auth = const FlutterAppAuth();
  final FlutterSecureStorage _storage;
  String? _access;
  String? _refresh;
  String? _idToken;
  DateTime? _expiry;
  bool get signedIn => _refresh != null;
  Future<void>? _refreshing;
  int _generation = 0;
  int get generation => _generation;
  Future<void> _storageTask = Future.value();

  // Queue credential writes and deletes so logout also clears a write already in progress.
  Future<void> _persist(Future<void> Function() operation) {
    final task = _storageTask.then((_) => operation());
    _storageTask = task.then<void>((_) {}, onError: (Object _) {});
    return task;
  }

  void _invalidate() {
    _generation++;
    _refreshing = null;
    _access = null;
    _refresh = null;
    _idToken = null;
    _expiry = null;
    notifyListeners();
  }

  Future<void> initialize() async {
    _refresh = await _storage.read(key: 'refresh_token');
    _idToken = await _storage.read(key: 'id_token');
  }

  Future<void> signIn() async {
    _invalidate();
    final generation = _generation;
    await _persist(() async {
      await _storage.delete(key: 'refresh_token');
      await _storage.delete(key: 'id_token');
    });
    if (generation != _generation) return;
    final result = await _auth.authorizeAndExchangeCode(
      AuthorizationTokenRequest(
        Env.clientId,
        Env.redirectUrl,
        discoveryUrl: Env.discoveryUrl,
        scopes: ['openid', 'email', 'profile', 'offline_access'],
        allowInsecureConnections: Env.localStaging,
      ),
    );
    if (generation != _generation) return;
    _generation++;
    await _save(result, _generation);
  }

  Future<void> _save(TokenResponse result, int generation) async {
    if (generation != _generation) return;
    if (result.accessToken == null) {
      throw StateError('Identity service did not return an access token');
    }
    _access = result.accessToken;
    _refresh = result.refreshToken ?? _refresh;
    _idToken = result.idToken ?? _idToken;
    _expiry = result.accessTokenExpirationDateTime;
    final idToken = _idToken;
    final refresh = _refresh;
    notifyListeners();
    await _persist(() async {
      if (generation != _generation) return;
      if (idToken != null) {
        await _storage.write(key: 'id_token', value: idToken);
      }
      if (refresh != null) {
        await _storage.write(key: 'refresh_token', value: refresh);
      }
    });
  }

  Future<String?> token() async {
    if (_access != null &&
        _expiry != null &&
        _expiry!.isAfter(DateTime.now().add(const Duration(seconds: 30)))) {
      return _access;
    }
    if (_refresh == null) return null;
    final generation = _generation;
    final refreshing = _refreshing ??= _refreshToken(generation);
    try {
      await refreshing;
    } finally {
      if (identical(_refreshing, refreshing)) _refreshing = null;
    }
    return generation == _generation ? _access : null;
  }

  Future<void> _refreshToken(int generation) async {
    try {
      final result = await _auth.token(
        TokenRequest(
          Env.clientId,
          Env.redirectUrl,
          refreshToken: _refresh,
          discoveryUrl: Env.discoveryUrl,
          scopes: ['openid', 'email', 'profile', 'offline_access'],
          allowInsecureConnections: Env.localStaging,
        ),
      );
      await _save(result, generation);
    } catch (_) {
      if (generation != _generation) return;
      // A transient provider outage must not erase the user's refresh identity.
      throw StateError(
        'Unable to refresh your session. Check your connection or sign in again.',
      );
    }
  }

  Future<void> signOut() async {
    final idToken = _idToken;
    _invalidate();
    await _persist(() async {
      await _storage.delete(key: 'refresh_token');
      await _storage.delete(key: 'id_token');
    });
    if (idToken != null) {
      await _auth.endSession(
        EndSessionRequest(
          idTokenHint: idToken,
          discoveryUrl: Env.discoveryUrl,
          allowInsecureConnections: Env.localStaging,
        ),
      );
    }
  }
}

import 'package:flutter/foundation.dart';
import 'package:flutter_appauth/flutter_appauth.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../config/env.dart';

class AccountSession extends ChangeNotifier {
  static final instance = AccountSession();
  final FlutterAppAuth _auth = const FlutterAppAuth();
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  String? _access;
  String? _refresh;
  String? _idToken;
  DateTime? _expiry;
  bool get signedIn => _refresh != null;
  Future<void>? _refreshing;

  Future<void> initialize() async {
    _refresh = await _storage.read(key: 'refresh_token');
  }
  Future<void> signIn() async {
    final result = await _auth.authorizeAndExchangeCode(AuthorizationTokenRequest(
      Env.clientId, Env.redirectUrl, discoveryUrl: Env.discoveryUrl,
      scopes: ['openid', 'email', 'profile', 'offline_access'],
      allowInsecureConnections: Env.localStaging));
    await _save(result);
  }
  Future<void> _save(TokenResponse result) async {
    if (result.accessToken == null) throw StateError('Identity service did not return an access token');
    _access = result.accessToken;
    _refresh = result.refreshToken ?? _refresh;
    _idToken = result.idToken;
    _expiry = result.accessTokenExpirationDateTime;
    if (_refresh != null) await _storage.write(key: 'refresh_token', value: _refresh);
    notifyListeners();
  }
  Future<String?> token() async {
    if (_access != null && _expiry != null && _expiry!.isAfter(DateTime.now().add(const Duration(seconds: 30)))) return _access;
    if (_refresh == null) return null;
    _refreshing ??= _refreshToken();
    try { await _refreshing; } finally { _refreshing = null; }
    return _access;
  }
  Future<void> _refreshToken() async {
    try {
      final result = await _auth.token(TokenRequest(Env.clientId, Env.redirectUrl,
        refreshToken: _refresh, discoveryUrl: Env.discoveryUrl, scopes: ['openid','email','profile','offline_access'],
        allowInsecureConnections: Env.localStaging));
      await _save(result);
    } catch (_) {
      // A transient provider outage must not erase the user's refresh identity.
      throw StateError('Unable to refresh your session. Check your connection or sign in again.');
    }
  }
  Future<void> signOut() async {
    final idToken = _idToken;
    _access = null; _refresh = null; _idToken = null; _expiry = null;
    await _storage.delete(key: 'refresh_token');
    notifyListeners();
    if (idToken != null) {
      await _auth.endSession(EndSessionRequest(idTokenHint: idToken,
        discoveryUrl: Env.discoveryUrl, allowInsecureConnections: Env.localStaging));
    }
  }
}

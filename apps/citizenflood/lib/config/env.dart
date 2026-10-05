/// Public API/OIDC config; private credentials never belong in a client build.
class Env {
  static const apiBase = String.fromEnvironment('API_BASE_URL');
  static const issuer = String.fromEnvironment('OIDC_ISSUER');
  static const discoveryUrl = String.fromEnvironment('OIDC_DISCOVERY_URL');
  static const clientId = String.fromEnvironment('OIDC_CLIENT_ID', defaultValue: 'citizen-mobile');
  static const redirectUrl = 'au.edu.monash.citizenflood:/oauthredirect';
  static const localStaging = bool.fromEnvironment('LOCAL_STAGING', defaultValue: false);
  static void assertConfigured() {
    for (final value in [apiBase, issuer, discoveryUrl]) {
      final uri = Uri.tryParse(value);
      if (uri == null || !uri.hasAuthority || (uri.scheme != 'https' && !(localStaging && uri.scheme == 'http' && ['localhost','127.0.0.1'].contains(uri.host)))) {
        throw StateError('Configure HTTPS API_BASE_URL, OIDC_ISSUER and OIDC_DISCOVERY_URL. Loopback HTTP is only allowed for local staging.');
      }
    }
  }
}

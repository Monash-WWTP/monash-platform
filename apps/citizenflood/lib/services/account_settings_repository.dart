import 'platform_api.dart';

class AccountSettings {
  AccountSettings(this.origin, this.actions);
  final Uri origin;
  final Map<String, Uri> actions;
  static const paths = {
    'profile': 'monash-account-profile',
    'email': 'monash-account-email',
    'password': 'monash-account-password',
    'security': 'monash-account-security',
    'sessions': 'monash-account-security',
    'signout_all': 'monash-account-signout-all',
  };
  static AccountSettings? parse(dynamic value) {
    if (value is! Map || value['available'] != true) return null;
    final origin = Uri.tryParse(value['origin'] ?? '');
    if (origin == null ||
        origin.host.isEmpty ||
        origin.userInfo.isNotEmpty ||
        origin.hasQuery ||
        origin.hasFragment ||
        (origin.path.isNotEmpty && origin.path != '/') ||
        (origin.scheme != 'https' &&
            !(origin.scheme == 'http' &&
                const [
                  'localhost',
                  '127.0.0.1',
                  '::1',
                ].contains(origin.host)))) {
      return null;
    }
    final actions = <String, Uri>{};
    final raw = value['actions'];
    if (raw is Map) {
      for (final entry in paths.entries) {
        final expected = origin.replace(path: '/if/flow/${entry.value}/');
        if (raw[entry.key] == expected.toString()) {
          actions[entry.key] = expected;
        }
      }
    }
    return AccountSettings(origin, actions);
  }
}

class AccountSettingsRepository {
  AccountSettingsRepository(this.api);
  final PlatformApi api;
  Future<AccountSettings?> load() async =>
      AccountSettings.parse(await api.request('/api/v1/auth/account-settings'));
}

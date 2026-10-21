import 'package:url_launcher/url_launcher.dart';
import 'account_settings_repository.dart';

class AccountSettingsLauncher {
  Future<bool> open(AccountSettings settings, String action) async {
    final uri = settings.actions[action];
    if (uri == null) return false;
    return launchUrl(uri, mode: LaunchMode.externalApplication);
  }
}

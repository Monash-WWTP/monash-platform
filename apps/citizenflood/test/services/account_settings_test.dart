import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/services/account_settings_repository.dart';

void main() {
  test('settings accept only same-origin approved flow paths', () {
    final settings = AccountSettings.parse({'available': true, 'origin': 'https://accounts.example.test', 'actions': {
      'profile': 'https://accounts.example.test/if/flow/monash-account-profile/',
      'email': 'https://evil.example/if/flow/monash-account-email/',
      'password': 'https://accounts.example.test/if/admin/',
    }});
    expect(settings!.actions.keys, ['profile']);
    expect(AccountSettings.parse({'available': true, 'origin': 'http://accounts.example.test'}), isNull);
    expect(AccountSettings.parse({'available': false}), isNull);
  });
}

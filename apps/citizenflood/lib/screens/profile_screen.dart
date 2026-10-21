import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/account_session.dart';
import '../services/platform_api.dart';
import '../services/account_settings_repository.dart';
import '../services/account_settings_launcher.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({
    super.key,
    this.session,
    this.api,
    this.settingsLauncher,
  });
  final AccountSession? session;
  final PlatformApi? api;
  final AccountSettingsLauncher? settingsLauncher;
  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen>
    with WidgetsBindingObserver {
  late final _session = widget.session ?? AccountSession.instance;
  late final _api = widget.api ?? PlatformApi();
  Future<dynamic>? _account;
  late int _generation;
  bool _busy = false;
  int? _settingsGeneration;
  String? _error;
  @override
  void initState() {
    super.initState();
    _generation = _session.generation;
    _load();
    WidgetsBinding.instance.addObserver(this);
    _session.addListener(_changed);
  }

  void _load() {
    _account = _session.signedIn ? _api.request('/api/v1/auth/me') : null;
  }

  void _changed() {
    if (_generation == _session.generation) return;
    _generation = _session.generation;
    setState(_load);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _session.removeListener(_changed);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state != AppLifecycleState.resumed || _settingsGeneration == null) {
      return;
    }
    final generation = _settingsGeneration!;
    _settingsGeneration = null;
    _refreshSettings(generation);
  }

  Future<void> _refreshSettings(int generation) async {
    if (generation != _session.generation || !_session.signedIn) return;
    try {
      await _session.refreshAccountProof();
      if (mounted && generation == _session.generation) setState(_load);
    } catch (_) {
      if (mounted && generation == _session.generation) {
        setState(
          () => _error = 'Could not refresh account details. Try again.',
        );
      }
    }
  }

  Future<void> _settings(String action) async {
    if (_busy) return;
    final generation = _session.generation;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final settings = await AccountSettingsRepository(_api).load();
      if (!mounted || generation != _session.generation) return;
      if (settings == null || !settings.actions.containsKey(action)) {
        throw StateError('Settings unavailable');
      }
      _settingsGeneration = generation;
      final opened =
          await (widget.settingsLauncher ?? AccountSettingsLauncher()).open(
            settings,
            action,
          );
      if (!opened) {
        _settingsGeneration = null;
        throw StateError('Could not open settings');
      }
    } catch (_) {
      _settingsGeneration = null;
      if (mounted && generation == _session.generation) {
        setState(
          () => _error = 'Account settings unavailable. Please try again.',
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _choices(List<(String, String, IconData)> actions) {
    showModalBottomSheet<void>(
      context: context,
      builder: (context) => SafeArea(
        child: ListView(
          shrinkWrap: true,
          children: [
            for (final action in actions)
              ListTile(
                leading: Icon(action.$3),
                title: Text(action.$1),
                onTap: () {
                  Navigator.pop(context);
                  _settings(action.$2);
                },
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _authenticate() async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await _session.signIn();
      if (mounted) setState(_load);
    } on PlatformException catch (e) {
      if (mounted) {
        setState(
          () => _error = e.code.toLowerCase().contains('cancel')
              ? 'Sign-in canceled. Your draft is still here.'
              : 'Could not complete sign-in. Check your connection and try again.',
        );
      }
    } catch (_) {
      if (mounted) {
        setState(
          () =>
              _error = 'Could not reach the account service. Please try again.',
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.all(24),
    children: [
      Align(
        alignment: Alignment.centerLeft,
        child: ClipRRect(
          borderRadius: BorderRadius.circular(16),
          child: Image.asset('assets/icon/icon.png', width: 64, height: 64),
        ),
      ),
      const SizedBox(height: 24),
      Text(
        _session.signedIn ? 'Your account' : 'Sign in to CitizenFlood',
        style: Theme.of(context).textTheme.headlineSmall,
      ),
      const SizedBox(height: 12),
      if (!_session.signedIn) ...[
        const Text('Save and track your reports.'),
        const SizedBox(height: 24),
        FilledButton(
          onPressed: _busy ? null : _authenticate,
          child: _busy
              ? const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                    SizedBox(width: 12),
                    Text('Opening secure sign-in…'),
                  ],
                )
              : const Text('Sign in / Create account'),
        ),
      ] else ...[
        FutureBuilder<dynamic>(
          key: ValueKey(_generation),
          future: _account,
          builder: (context, snapshot) {
            if (snapshot.hasError) {
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Account details unavailable.'),
                  TextButton(
                    onPressed: () => setState(_load),
                    child: const Text('Retry account details'),
                  ),
                ],
              );
            }
            if (!snapshot.hasData) {
              return const Padding(
                padding: EdgeInsets.symmetric(vertical: 16),
                child: LinearProgressIndicator(),
              );
            }
            final account = snapshot.data;
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (account['display_name'] is String &&
                    (account['display_name'] as String).isNotEmpty)
                  Text(
                    account['display_name'],
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                Text(
                  account['email'] ?? 'Signed in',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                const Row(
                  children: [
                    Icon(Icons.verified_user_outlined, size: 18),
                    SizedBox(width: 8),
                    Expanded(child: Text('Verified account')),
                  ],
                ),
              ],
            );
          },
        ),
        const SizedBox(height: 24),
        Text(
          'Opens secure account settings',
          style: Theme.of(context).textTheme.bodySmall,
        ),
        ListTile(
          leading: const Icon(Icons.person_outline),
          title: const Text('Profile'),
          onTap: _busy ? null : () => _settings('profile'),
        ),
        ListTile(
          leading: const Icon(Icons.mail_outline),
          title: const Text('Email & password'),
          onTap: _busy
              ? null
              : () => _choices([
                  ('Change email', 'email', Icons.mail_outline),
                  ('Change password', 'password', Icons.lock_outline),
                ]),
        ),
        ListTile(
          leading: const Icon(Icons.shield_outlined),
          title: const Text('Security'),
          onTap: _busy
              ? null
              : () => _choices([
                  ('MFA & account sessions', 'security', Icons.shield_outlined),
                  ('Sign out all devices', 'signout_all', Icons.logout),
                ]),
        ),
        OutlinedButton(
          onPressed: _busy
              ? null
              : () async {
                  setState(() => _busy = true);
                  try {
                    await _session.signOut();
                  } finally {
                    if (mounted) setState(() => _busy = false);
                  }
                },
          child: const Text('Sign out'),
        ),
      ],
      if (_error != null)
        Padding(
          padding: const EdgeInsets.only(top: 16),
          child: Text(
            _error!,
            style: TextStyle(color: Theme.of(context).colorScheme.error),
          ),
        ),
      const SizedBox(height: 36),
      const Divider(),
      const ExpansionTile(
        title: Text('About CitizenFlood'),
        tilePadding: EdgeInsets.zero,
        children: [
          Padding(
            padding: EdgeInsets.only(bottom: 16),
            child: Text(
              'Public locations are rounded for privacy. Citizen observations are not laboratory measurements.',
            ),
          ),
        ],
      ),
    ],
  );
}

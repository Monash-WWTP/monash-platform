import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/account_session.dart';
import '../services/platform_api.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key, this.session, this.api});
  final AccountSession? session;
  final PlatformApi? api;
  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  late final _session = widget.session ?? AccountSession.instance;
  late final _api = widget.api ?? PlatformApi();
  Future<dynamic>? _account;
  late int _generation;
  bool _busy = false;
  String? _error;
  @override
  void initState() {
    super.initState();
    _generation = _session.generation;
    _load();
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
    _session.removeListener(_changed);
    super.dispose();
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
                Text(
                  account['email'] ?? 'Signed in',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                const Row(
                  children: [
                    Icon(Icons.verified_user_outlined, size: 18),
                    SizedBox(width: 8),
                    Text('Verified account'),
                  ],
                ),
              ],
            );
          },
        ),
        const SizedBox(height: 24),
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

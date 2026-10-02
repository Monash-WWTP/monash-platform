import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final user = Supabase.instance.client.auth.currentUser;
    final isAnonymous = user?.isAnonymous ?? true;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const SizedBox(height: 8),
        const CircleAvatar(radius: 36, child: Icon(Icons.person, size: 36)),
        const SizedBox(height: 12),
        Center(
          child: Text(
            isAnonymous
                ? 'Reporting anonymously'
                : (user?.email ?? 'Signed in'),
            style: Theme.of(context).textTheme.titleMedium,
          ),
        ),
        const SizedBox(height: 24),
        Card(
          child: ListTile(
            leading: const Icon(Icons.info_outline),
            title: const Text('About CitizenFlood'),
            subtitle: const Text(
              'Report flooding, rain, and water levels in your area. '
              'Your reports help researchers and your community stay safe.',
            ),
          ),
        ),
        if (isAnonymous)
          Card(
            child: ListTile(
              leading: const Icon(Icons.mail_outline),
              title: const Text('Sign in with email (optional)'),
              subtitle: const Text(
                'Optional — lets you keep your reports if you change phones.',
              ),
              onTap: () => _promptEmailSignIn(context),
            ),
          ),
      ],
    );
  }

  Future<void> _promptEmailSignIn(BuildContext context) async {
    final controller = TextEditingController();
    final email = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Sign in with email'),
        content: TextField(
          controller: controller,
          keyboardType: TextInputType.emailAddress,
          decoration: const InputDecoration(hintText: 'you@example.com'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, controller.text.trim()),
            child: const Text('Send link'),
          ),
        ],
      ),
    );
    if (email == null || email.isEmpty) return;
    try {
      await Supabase.instance.client.auth.signInWithOtp(email: email);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Check your email for a sign-in link.')),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Could not send link: $e')));
      }
    }
  }
}

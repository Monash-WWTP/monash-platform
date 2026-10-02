import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'config/env.dart';
import 'theme/app_theme.dart';
import 'screens/home_shell.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  Env.assertConfigured();

  await Supabase.initialize(
    url: Env.supabaseUrl,
    // The Supabase "anon public" key is the publishable key in newer SDKs.
    publishableKey: Env.supabaseAnonKey,
  );

  // Ensure every citizen has an identity (required by our insert policy).
  final auth = Supabase.instance.client.auth;
  if (auth.currentUser == null) {
    await auth.signInAnonymously();
  }

  runApp(const CitizenFloodApp());
}

class CitizenFloodApp extends StatelessWidget {
  const CitizenFloodApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'CitizenFlood',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      home: const HomeShell(),
    );
  }
}

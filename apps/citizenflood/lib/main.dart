import 'package:flutter/material.dart';
import 'services/account_session.dart';

import 'config/env.dart';
import 'theme/app_theme.dart';
import 'screens/home_shell.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  Env.assertConfigured();

  await AccountSession.instance.initialize();

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

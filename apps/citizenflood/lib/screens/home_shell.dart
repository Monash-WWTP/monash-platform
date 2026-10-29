import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import '../services/depth_preview.dart';
import '../services/account_session.dart';
import 'map_screen.dart';
import 'my_reports_screen.dart';
import 'profile_screen.dart';

class HomeShell extends StatefulWidget {
  const HomeShell({super.key, this.session});
  final AccountSession? session;
  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _index = 0;
  bool _openingCamera = false;
  late final _session = widget.session ?? AccountSession.instance;
  late int _generation = _session.generation;
  @override
  void initState() {
    super.initState();
    _session.addListener(_accountChanged);
  }

  void _accountChanged() {
    if (_generation == _session.generation) return;
    _generation = _session.generation;
    unawaited(DepthPreview.close().catchError((Object _) {}));
  }

  @override
  void dispose() {
    _session.removeListener(_accountChanged);
    unawaited(DepthPreview.close().catchError((Object _) {}));
    super.dispose();
  }

  Future<void> _cameraWater() async {
    final generation = _generation;
    setState(() => _openingCamera = true);
    try {
      await DepthPreview.openCameraFilter();
      if (!mounted || generation != _generation) await DepthPreview.close();
    } catch (_) {
      if (mounted && generation == _generation) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Camera could not open. Please retry.')),
        );
      }
    } finally {
      if (mounted) setState(() => _openingCamera = false);
    }
  }

  static const _titles = ['CitizenFlood', 'My reports', 'Account'];
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(
      centerTitle: false,
      actions: [
        if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android)
          IconButton(
            tooltip: 'Camera water',
            icon: const Icon(Icons.camera_alt_outlined),
            onPressed: _openingCamera ? null : _cameraWater,
          ),
      ],
      title: Row(
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: Image.asset('assets/icon/icon.png', width: 32, height: 32),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              _titles[_index],
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    ),
    body: IndexedStack(
      index: _index,
      children: [
        MapScreen(onShowReports: () => setState(() => _index = 1)),
        MyReportsScreen(active: _index == 1),
        const ProfileScreen(),
      ],
    ),
    bottomNavigationBar: NavigationBar(
      selectedIndex: _index,
      onDestinationSelected: (i) => setState(() => _index = i),
      destinations: const [
        NavigationDestination(
          icon: Icon(Icons.map_outlined),
          selectedIcon: Icon(Icons.map),
          label: 'Map',
        ),
        NavigationDestination(
          icon: Icon(Icons.receipt_long_outlined),
          selectedIcon: Icon(Icons.receipt_long),
          label: 'My reports',
        ),
        NavigationDestination(
          icon: Icon(Icons.person_outline),
          selectedIcon: Icon(Icons.person),
          label: 'Account',
        ),
      ],
    ),
  );
}

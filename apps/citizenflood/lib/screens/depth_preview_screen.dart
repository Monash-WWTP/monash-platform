import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/depth_preview.dart';
import '../services/account_session.dart';

class DepthPreviewScreen extends StatefulWidget {
  const DepthPreviewScreen({
    super.key,
    required this.preview,
    required this.contextLabel,
    this.session,
  });
  final DepthPreview preview;
  final String contextLabel;
  final AccountSession? session;
  @override
  State<DepthPreviewScreen> createState() => _DepthPreviewScreenState();
}

class _DepthPreviewScreenState extends State<DepthPreviewScreen> {
  late final _session = widget.session ?? AccountSession.instance;
  late final int _generation;
  bool _invalidated = false;
  final _scroll = ScrollController();
  @override
  void initState() {
    super.initState();
    _generation = _session.generation;
    _session.addListener(_accountChanged);
  }

  void _accountChanged() {
    if (_session.generation == _generation || _invalidated) return;
    setState(() => _invalidated = true);
    unawaited(DepthPreview.close().catchError((Object _) {}));
  }

  @override
  void dispose() {
    _session.removeListener(_accountChanged);
    _scroll.dispose();
    // The parent reporting route can also be dismissed by account invalidation.
    unawaited(DepthPreview.close().catchError((Object _) {}));
    super.dispose();
  }

  bool _opening = false;
  String? _error;
  Future<void> _open({
    bool threeDimensional = false,
    bool cameraFilter = false,
  }) async {
    if (_invalidated) return;
    setState(() {
      _opening = true;
      _error = null;
    });
    try {
      if (cameraFilter) {
        await widget.preview.openCamera(contextLabel: widget.contextLabel);
      } else if (threeDimensional) {
        await widget.preview.open3d(contextLabel: widget.contextLabel);
      } else {
        await widget.preview.open(contextLabel: widget.contextLabel);
      }
    } on MissingPluginException {
      if (mounted) {
        setState(
          () => _error =
              'Water preview is unavailable in this build. You can continue reporting normally.',
        );
      }
    } on PlatformException catch (e) {
      if (mounted) {
        setState(
          () => _error =
              e.message ??
              'Preview could not open. You can continue reporting normally.',
        );
      }
    } finally {
      if (mounted) {
        setState(() => _opening = false);
        if (_error != null && _scroll.hasClients) _scroll.jumpTo(0);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_invalidated) {
      return Scaffold(
        appBar: AppBar(title: const Text('Preview closed')),
        body: const SafeArea(
          child: Padding(
            padding: EdgeInsets.all(24),
            child: Text(
              'Your account changed. Return to your reports to start a new preview.',
            ),
          ),
        ),
      );
    }
    final supported =
        !kIsWeb && defaultTargetPlatform == TargetPlatform.android;
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Visualise reported depth')),
      body: SafeArea(
        child: ListView(
          controller: _scroll,
          padding: const EdgeInsets.all(24),
          children: [
            Text(
              '${widget.preview.depthM} m',
              style: theme.textTheme.headlineLarge,
            ),
            const SizedBox(height: 8),
            Text(widget.contextLabel),
            const SizedBox(height: 24),
            Text(
              'Reference: ${widget.preview.reference}',
              style: theme.textTheme.titleMedium,
            ),
            const SizedBox(height: 16),
            const Text(
              'This illustrates your entered depth. It does not measure water or predict flooding.',
            ),
            const SizedBox(height: 16),
            if (!supported)
              const Text(
                'Water previews are available on Android. Reporting remains available.',
              ),
            if (_error != null) ...[
              Semantics(
                liveRegion: true,
                child: Text(
                  _error!,
                  style: TextStyle(color: theme.colorScheme.error),
                ),
              ),
              const SizedBox(height: 16),
            ],
            FilledButton.icon(
              onPressed: supported && !_opening
                  ? () => _open(cameraFilter: true)
                  : null,
              icon: const Icon(Icons.camera_alt_outlined),
              label: const Text('Camera water'),
            ),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: supported && !_opening
                  ? () => _open(threeDimensional: true)
                  : null,
              icon: const Icon(Icons.water),
              label: const Text('3D water preview'),
            ),
            const Text(
              'Rotate and zoom an illustrative scene. No camera needed.',
            ),
            const SizedBox(height: 16),
            const Divider(height: 32),
            Text('AR in your surroundings', style: theme.textTheme.titleMedium),
            const SizedBox(height: 16),
            const Text(
              'Choose a visible, safe surface matching this reference. The camera will help place the illustration above it. If the reference is submerged or inaccessible, skip the preview. Never enter floodwater.',
            ),
            const SizedBox(height: 16),
            const Text(
              'AR preview uses Google Play Services for AR (ARCore). Google provides this service and processes data under its Privacy Policy.',
            ),
            TextButton(
              onPressed: () async {
                try {
                  final opened = await launchUrl(
                    Uri.parse('https://policies.google.com/privacy'),
                    mode: LaunchMode.externalApplication,
                  );
                  if (!opened && mounted) {
                    setState(
                      () => _error =
                          'Could not open the Google Privacy Policy. Visit policies.google.com/privacy in your browser.',
                    );
                  }
                } catch (_) {
                  if (mounted) {
                    setState(
                      () => _error =
                          'Could not open the Google Privacy Policy. Visit policies.google.com/privacy in your browser.',
                    );
                  }
                }
              },
              child: const Text('Google Privacy Policy'),
            ),
            const SizedBox(height: 16),
            const Text(
              'Camera frames are not uploaded by this preview. No rendered image is attached to your report. A past report is illustrated in your current surroundings, not reconstructed.',
            ),
            const SizedBox(height: 24),
            OutlinedButton.icon(
              onPressed: supported && !_opening ? () => _open() : null,
              icon: const Icon(Icons.view_in_ar),
              label: Text(_opening ? 'Opening camera…' : 'Open AR preview'),
            ),
            const SizedBox(height: 8),
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Return to report'),
            ),
          ],
        ),
      ),
    );
  }
}

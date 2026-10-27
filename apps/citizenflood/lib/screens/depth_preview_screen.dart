import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/depth_preview.dart';

class DepthPreviewScreen extends StatefulWidget {
  const DepthPreviewScreen({
    super.key,
    required this.preview,
    required this.contextLabel,
  });
  final DepthPreview preview;
  final String contextLabel;
  @override
  State<DepthPreviewScreen> createState() => _DepthPreviewScreenState();
}

class _DepthPreviewScreenState extends State<DepthPreviewScreen> {
  bool _opening = false;
  String? _error;
  Future<void> _open() async {
    setState(() {
      _opening = true;
      _error = null;
    });
    try {
      await widget.preview.open(contextLabel: widget.contextLabel);
    } on MissingPluginException {
      if (mounted) {
        setState(
          () => _error =
              'AR preview is unavailable in this build. You can continue reporting normally.',
        );
      }
    } on PlatformException catch (e) {
      if (mounted) {
        setState(
          () => _error =
              e.message ??
              'AR could not open. You can continue reporting normally.',
        );
      }
    } finally {
      if (mounted) setState(() => _opening = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final supported =
        !kIsWeb && defaultTargetPlatform == TargetPlatform.android;
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Visualise reported depth')),
      body: SafeArea(
        child: ListView(
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
            const Text(
              'Choose a visible, safe surface matching this reference. The camera will help place the illustration above it. If the reference is submerged or inaccessible, skip the preview. Never enter floodwater.',
            ),
            const SizedBox(height: 16),
            const Text(
              'Camera frames are not uploaded by this preview. No rendered image is attached to your report. A past report is illustrated in your current surroundings, not reconstructed.',
            ),
            const SizedBox(height: 24),
            if (!supported)
              const Text(
                'AR preview is available on compatible Android phones. Reporting remains available.',
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
              onPressed: supported && !_opening ? _open : null,
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

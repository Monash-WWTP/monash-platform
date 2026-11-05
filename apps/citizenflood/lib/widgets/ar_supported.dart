import 'package:flutter/material.dart';
import '../services/depth_preview.dart';

class ArSupported extends StatefulWidget {
  const ArSupported({super.key, required this.child});
  final Widget child;
  @override
  State<ArSupported> createState() => _ArSupportedState();
}

class _ArSupportedState extends State<ArSupported> {
  final _supported = DepthPreview.isSupported();
  @override
  Widget build(BuildContext context) => FutureBuilder<bool>(
    future: _supported,
    builder: (context, snapshot) =>
        snapshot.data == true ? widget.child : const SizedBox.shrink(),
  );
}

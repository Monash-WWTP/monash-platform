import 'package:flutter/services.dart';

/// A reported distance above a described surface, never a gauge elevation.
class DepthPreview {
  const DepthPreview._(this.depthM, this.reference);
  final double depthM;
  final String reference;
  static const channel = MethodChannel('citizenflood/depth_preview');

  static DepthPreview? fromObservation(Map<String, dynamic>? data) {
    if (data == null ||
        data['kind'] != 'water_reading' ||
        data['reference_kind'] != 'depth' ||
        data['unit'] != 'm') {
      return null;
    }
    final value = data['value'];
    final reference = data['reference_description'];
    if (value is! num ||
        !value.isFinite ||
        value < 0 ||
        reference is! String ||
        reference.trim().isEmpty) {
      return null;
    }
    return DepthPreview._(value.toDouble(), reference.trim());
  }

  Future<void> open({required String contextLabel}) =>
      channel.invokeMethod<void>('open', {
        'depthM': depthM,
        'reference': reference,
        'contextLabel': contextLabel,
      });
}

import '../models/observation.dart';
import 'platform_api.dart';

class ObservationRepository {
  ObservationRepository([PlatformApi? api]) : _api = api ?? PlatformApi();
  final PlatformApi _api;
  Future<bool>? _supported;
  Set<int> _revisions = {1};
  Future<bool> supportsRevision(int revision) async =>
      await supported() && _revisions.contains(revision);
  Future<bool> supported() {
    if (_supported != null) return _supported!;
    final future = _discover();
    _supported = future;
    future.then<void>(
      (supported) {
        if (!supported && identical(_supported, future)) _supported = null;
      },
      onError: (Object error, StackTrace stack) {
        if (identical(_supported, future)) _supported = null;
      },
    );
    return future;
  }

  Future<bool> _discover() async {
    try {
      final c = await _api.request('/api/v2/observation-protocols');
      _revisions = {
        1,
        ...((c['supported_revisions'] as List?) ?? []).whereType<int>(),
      };
      return c['protocol_id'] == 'citizen-observation' &&
          c['protocol_revision'] == 1 &&
          (c['types'] is List) &&
          observationLabels.keys.every((k) => (c['types'] as List).contains(k));
    } on ApiRequestException catch (e) {
      if (e.status == 404) return false;
      rethrow;
    }
  }

  void retryDiscovery() => _supported = null;
  Future<List<Map<String, dynamic>>> references() async {
    final p = await _api.request('/api/v2/observation-references');
    return (p['items'] as List)
        .map((r) => Map<String, dynamic>.from(r))
        .toList();
  }

  Future<void> submit(ObservationDraft draft, String key) async {
    if (!await supportsRevision(draft.payload['protocol_revision'] as int)) {
      throw StateError(
        'This service does not support the new reporting protocol yet.',
      );
    }
    await _api.request(
      '/api/v2/observations',
      method: 'POST',
      body: draft.payload,
      headers: {'Idempotency-Key': key},
    );
  }
}

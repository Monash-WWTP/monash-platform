import 'platform_api.dart';

class MonitoringStation {
  const MonitoringStation({
    required this.code,
    required this.name,
    required this.latitude,
    required this.longitude,
    this.process,
  });
  final String code, name;
  final double latitude, longitude;
  final String? process;
  factory MonitoringStation.fromJson(Map<String, dynamic> row) =>
      MonitoringStation(
        code: row['code'] as String,
        name: row['name'] as String,
        latitude: (row['latitude'] as num).toDouble(),
        longitude: (row['longitude'] as num).toDouble(),
        process: row['stp_type'] as String?,
      );
}

/// Laboratory monitoring is separate from citizen observations and simulations.
class StationRepository {
  StationRepository({PlatformApi? api}) : _api = api ?? PlatformApi();
  final PlatformApi _api;
  Future<List<Map<String, dynamic>>> _pages(String path) async {
    final rows = <Map<String, dynamic>>[];
    var offset = 0;
    while (true) {
      final page = await _api.request(
        '$path${path.contains('?') ? '&' : '?'}limit=500&offset=$offset',
      );
      final items = (page['items'] as List)
          .map((r) => Map<String, dynamic>.from(r as Map))
          .toList();
      rows.addAll(items);
      offset += items.length;
      if (offset >= (page['total'] as int)) return rows;
      if (items.isEmpty) {
        throw StateError('Incomplete monitoring response. Please retry.');
      }
    }
  }

  Future<List<MonitoringStation>> stations() async => [
    for (final row in await _pages('/api/v1/monitoring/stations'))
      MonitoringStation.fromJson(row),
  ];
  Future<Map<String, dynamic>?> latestSample(String code) async {
    final rows = await _pages(
      '/api/v1/monitoring/samples?station_code=${Uri.encodeQueryComponent(code)}',
    );
    rows.sort(
      (a, b) =>
          (b['sample_date'] as String).compareTo(a['sample_date'] as String),
    );
    return rows.firstOrNull;
  }
}

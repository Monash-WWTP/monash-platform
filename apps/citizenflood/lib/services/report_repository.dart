import 'dart:typed_data';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../models/report.dart';

class ReportRepository {
  ReportRepository([SupabaseClient? client])
    : _client = client ?? Supabase.instance.client;

  final SupabaseClient _client;
  static const _table = 'citizen_reports';
  static const _publicView = 'approved_citizen_observations';
  static const _bucket = 'citizen-report-photos';

  /// Uploads a photo's bytes and returns its storage path.
  Future<String> uploadPhoto(Uint8List bytes, String fileExtension) async {
    final userId = _client.auth.currentUser!.id;
    final ext = fileExtension.toLowerCase();
    final path = '$userId/${DateTime.now().millisecondsSinceEpoch}.$ext';
    await _client.storage
        .from(_bucket)
        .uploadBinary(
          path,
          bytes,
          fileOptions: FileOptions(contentType: _mimeFor(ext)),
        );
    return path;
  }

  static String _mimeFor(String ext) => switch (ext) {
    'png' => 'image/png',
    'webp' => 'image/webp',
    'heic' => 'image/heic',
    'heif' => 'image/heif',
    'gif' => 'image/gif',
    _ => 'image/jpeg', // jpg/jpeg and any unknown image fall back to jpeg
  };

  /// Short-lived URL for a photo owned by the current user.
  Future<String> photoUrl(String path) =>
      _client.storage.from(_bucket).createSignedUrl(path, 600);

  /// Inserts a report row.
  Future<void> submit(Report report) async {
    await _client.from(_table).insert(report.toInsertMap());
  }

  /// Fetches approved public observations plus the current citizen's pending
  /// reports. The database view excludes reporter and moderation details.
  Future<List<Report>> recent({int limit = 200}) async {
    final publicRows = await _client
        .from(_publicView)
        .select()
        .order('observed_at', ascending: false)
        .limit(limit);

    final userId = _client.auth.currentUser?.id;
    final ownRows = userId == null
        ? <Map<String, dynamic>>[]
        : (await _client
                  .from(_table)
                  .select(
                    'id, category, reading_value, reading_unit, condition, note, '
                    'latitude, longitude, location_accuracy_m, station_code, '
                    'photo_path, observed_at, moderation_status, created_at',
                  )
                  .eq('reporter_id', userId)
                  .order('observed_at', ascending: false)
                  .limit(limit))
              .cast<Map<String, dynamic>>();

    final byId = <String, Report>{};
    for (final row in (publicRows as List)) {
      final report = Report.fromRow(row as Map<String, dynamic>);
      if (report.id != null) byId[report.id!] = report;
    }
    // Prefer the owner's row because it may contain their private photo path
    // and current moderation state.
    for (final row in ownRows) {
      final report = Report.fromRow(row);
      if (report.id != null) byId[report.id!] = report;
    }

    final reports = byId.values.toList()
      ..sort((a, b) {
        final ad =
            a.observedAt ??
            a.createdAt ??
            DateTime.fromMillisecondsSinceEpoch(0);
        final bd =
            b.observedAt ??
            b.createdAt ??
            DateTime.fromMillisecondsSinceEpoch(0);
        return bd.compareTo(ad);
      });
    return reports.take(limit).toList();
  }
}

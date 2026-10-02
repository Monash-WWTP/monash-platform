import 'dart:typed_data';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:uuid/uuid.dart';
import '../models/report.dart';
import '../config/env.dart';
import 'account_session.dart';
import 'platform_api.dart';

class ReportRepository {
  ReportRepository([PlatformApi? api]) : _api = api ?? PlatformApi();
  final PlatformApi _api;
  Future<String> uploadPhoto(Uint8List bytes, String fileExtension) async {
    final token = await AccountSession.instance.token();
    if (token == null) throw StateError('Sign in with a verified account to attach a photo.');
    final request = http.MultipartRequest('POST', Uri.parse('${Env.apiBase}/api/v1/media'));
    request.headers['Authorization'] = 'Bearer $token';
    request.files.add(http.MultipartFile.fromBytes('file',bytes,filename:'photo.$fileExtension'));
    final response = await http.Response.fromStream(await request.send().timeout(const Duration(seconds:30)));
    final decoded = jsonDecode(response.body);
    if (response.statusCode != 201) throw StateError(decoded['error']?['message'] ?? 'Photo upload failed');
    return decoded['id'] as String;
  }
  Future<Uint8List> photoBytes(String mediaId) async {
    final token = await AccountSession.instance.token();
    final response = await http.get(Uri.parse('${Env.apiBase}/api/v1/media/$mediaId'),
      headers: {if(token != null)'Authorization':'Bearer $token'}).timeout(const Duration(seconds:15));
    if (response.statusCode != 200) throw StateError('Photo unavailable');
    return response.bodyBytes;
  }
  Future<void> submit(Report report, {String? idempotencyKey}) async {
    final data = report.toInsertMap();
    data['media_id'] = data.remove('photo_path');
    await _api.request('/api/v1/reports',method:'POST',body:data,
      headers:{'Idempotency-Key':idempotencyKey ?? const Uuid().v4()});
  }
  Future<List<Report>> recent({int limit = 200}) async {
    final public = await _api.request('/api/v1/community/observations?limit=$limit');
    final rows = <String,Report>{};
    for (final row in public['items']) {
      final report = Report.fromRow(Map<String,dynamic>.from(row));
      rows[report.id!] = report;
    }
    if (AccountSession.instance.signedIn) {
      final own = await _api.request('/api/v1/reports?limit=$limit');
      for (final raw in own['items']) {
        final row = Map<String,dynamic>.from(raw); row['photo_path'] = row.remove('media_id');
        final report = Report.fromRow(row); rows[report.id!] = report;
      }
    }
    return rows.values.toList()..sort((a,b)=>(b.observedAt ?? DateTime(1970)).compareTo(a.observedAt ?? DateTime(1970)));
  }
}

import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/env.dart';
import 'account_session.dart';

class PlatformApi {
  PlatformApi({http.Client? client, Future<String?> Function()? token, String? baseUrl})
    : client = client ?? http.Client(), token = token ?? AccountSession.instance.token, baseUrl = baseUrl ?? Env.apiBase;
  final String baseUrl;
  final http.Client client;
  final Future<String?> Function() token;
  Future<dynamic> request(String path, {String method = 'GET', Object? body, Map<String,String>? headers}) async {
    final access = await token();
    final request = http.Request(method, Uri.parse('$baseUrl$path'));
    request.headers.addAll({'Content-Type':'application/json',if(access != null)'Authorization':'Bearer $access',...?headers});
    if (body != null) request.body = jsonEncode(body);
    final response = await http.Response.fromStream(await client.send(request).timeout(const Duration(seconds: 15)));
    if (response.statusCode >= 400) {
      final decoded = jsonDecode(response.body);
      throw StateError(decoded['error']?['message'] ?? 'Request failed (${response.statusCode})');
    }
    return response.statusCode == 204 ? null : jsonDecode(response.body);
  }
}

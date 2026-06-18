import 'dart:convert';
import 'package:http/http.dart' as http;
import 'auth.dart';

Future<Map<String, dynamic>> callKiwoom(
  String realPath,
  String apiId,
  Map<String, dynamic> body,
) async {
  final token = await getToken();
  final base = getBaseUrl();

  final res = await http.post(
    Uri.parse('$base$realPath'),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
      'api-id': apiId,
    },
    body: jsonEncode(body),
  );

  final data = jsonDecode(res.body) as Map<String, dynamic>;

  if (res.statusCode != 200) {
    throw StateError('Kiwoom API error (${res.statusCode}): ${res.body}');
  }

  return data;
}

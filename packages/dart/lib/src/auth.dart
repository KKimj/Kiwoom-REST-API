import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

String getBaseUrl() {
  final env = Platform.environment['KIWOOM_ENV'] ?? 'mock';
  return env == 'live'
      ? 'https://api.kiwoom.com'
      : 'https://mockapi.kiwoom.com';
}

String? _cachedToken;
DateTime? _expiresAt;

DateTime _parseExpiresDt(String dt) {
  final y = int.parse(dt.substring(0, 4));
  final mo = int.parse(dt.substring(4, 6));
  final d = int.parse(dt.substring(6, 8));
  final h = int.parse(dt.substring(8, 10));
  final mi = int.parse(dt.substring(10, 12));
  final s = int.parse(dt.substring(12, 14));
  return DateTime(y, mo, d, h, mi, s);
}

Future<String> getToken() async {
  final direct = Platform.environment['KIWOOM_ACCESS_TOKEN'];
  if (direct != null && direct.isNotEmpty) return direct;

  final now = DateTime.now();
  final expires = _expiresAt;
  if (_cachedToken != null &&
      expires != null &&
      now.isBefore(expires.subtract(const Duration(minutes: 5)))) {
    return _cachedToken!;
  }

  final appKey = Platform.environment['KIWOOM_APP_KEY'];
  final appSecret = Platform.environment['KIWOOM_APP_SECRET'];
  if (appKey == null || appSecret == null) {
    throw StateError(
        'KIWOOM_APP_KEY and KIWOOM_APP_SECRET environment variables are required');
  }

  final res = await http.post(
    Uri.parse('${getBaseUrl()}/oauth2/token/au10001'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'grant_type': 'client_credentials',
      'appkey': appKey,
      'appsecretkey': appSecret,
    }),
  );

  if (res.statusCode != 200) {
    throw StateError('Token fetch failed (${res.statusCode}): ${res.body}');
  }

  final data = jsonDecode(res.body) as Map<String, dynamic>;
  _cachedToken = data['access_token'] as String;
  _expiresAt = _parseExpiresDt(data['expires_dt'] as String);
  return _cachedToken!;
}

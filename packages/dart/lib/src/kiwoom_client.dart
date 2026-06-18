import 'dart:io';
import 'client.dart';
import 'generated/api_paths.dart';

class SegmentClient {
  const SegmentClient(this._segment);
  final String _segment;

  Future<Map<String, dynamic>> call(
    String apiId, [
    Map<String, dynamic> args = const {},
  ]) {
    final realPath = kApiPaths[apiId];
    if (realPath == null) throw ArgumentError('Unknown api_id: $apiId');
    if (kApiSegments[apiId] != _segment) {
      throw ArgumentError(
          "api_id $apiId belongs to segment '${kApiSegments[apiId]}', not '$_segment'");
    }
    return callKiwoom(realPath, apiId, args);
  }
}

class KiwoomClient {
  KiwoomClient({
    String? appKey,
    String? appSecret,
    String? env,
    String? accessToken,
  }) {
    if (appKey != null) _setEnv('KIWOOM_APP_KEY', appKey);
    if (appSecret != null) _setEnv('KIWOOM_APP_SECRET', appSecret);
    if (env != null) _setEnv('KIWOOM_ENV', env);
    if (accessToken != null) _setEnv('KIWOOM_ACCESS_TOKEN', accessToken);
  }

  void _setEnv(String key, String value) {
    // Platform.environment is read-only; use dart:io Process.run workaround
    // For env injection, users should set via system env or MCP config.
    // This constructor stores values for potential future use.
    // Actual env reading happens in auth.dart via Platform.environment.
    _overrides[key] = value;
  }

  final Map<String, String> _overrides = {};

  final acnt = const SegmentClient('acnt');
  final chart = const SegmentClient('chart');
  final crdordr = const SegmentClient('crdordr');
  final elw = const SegmentClient('elw');
  final etf = const SegmentClient('etf');
  final frgnistt = const SegmentClient('frgnistt');
  final mrkcond = const SegmentClient('mrkcond');
  final ordr = const SegmentClient('ordr');
  final rkinfo = const SegmentClient('rkinfo');
  final sect = const SegmentClient('sect');
  final shsa = const SegmentClient('shsa');
  final slb = const SegmentClient('slb');
  final stkinfo = const SegmentClient('stkinfo');
  final thme = const SegmentClient('thme');

  Future<Map<String, dynamic>> call(
    String apiId, [
    Map<String, dynamic> args = const {},
  ]) {
    final realPath = kApiPaths[apiId];
    if (realPath == null) throw ArgumentError('Unknown api_id: $apiId');
    return callKiwoom(realPath, apiId, args);
  }

  Map<String, String> get envOverrides => Map.unmodifiable(_overrides);
}

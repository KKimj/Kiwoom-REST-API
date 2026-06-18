import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'generated/tools.dart';

Future<void> runMcpServer() async {
  final input = stdin
      .transform(utf8.decoder)
      .transform(const LineSplitter());

  await for (final line in input) {
    final trimmed = line.trim();
    if (trimmed.isEmpty) continue;

    Map<String, dynamic> request;
    try {
      request = jsonDecode(trimmed) as Map<String, dynamic>;
    } catch (_) {
      continue;
    }

    final response = await _handle(request);
    if (response != null) {
      stdout.writeln(jsonEncode(response));
    }
  }
}

Future<Map<String, dynamic>?> _handle(Map<String, dynamic> req) async {
  final id = req['id'];
  final method = req['method'] as String?;

  switch (method) {
    case 'initialize':
      return {
        'jsonrpc': '2.0',
        'id': id,
        'result': {
          'protocolVersion': '2024-11-05',
          'capabilities': {'tools': <String, dynamic>{}},
          'serverInfo': {'name': 'kiwoom-rest-api', 'version': '0.1.0'},
        },
      };

    case 'notifications/initialized':
      return null;

    case 'tools/list':
      return {
        'jsonrpc': '2.0',
        'id': id,
        'result': {
          'tools': kTools
              .map((t) => {
                    'name': t.name,
                    'description': t.description,
                    'inputSchema': t.inputSchema,
                  })
              .toList(),
        },
      };

    case 'tools/call':
      final params = req['params'] as Map<String, dynamic>? ?? {};
      final toolName = params['name'] as String?;
      final args = (params['arguments'] as Map<String, dynamic>?) ?? {};

      final tool = kTools.where((t) => t.name == toolName).firstOrNull;
      if (tool == null) {
        return {
          'jsonrpc': '2.0',
          'id': id,
          'result': {
            'content': [
              {'type': 'text', 'text': 'Unknown tool: $toolName'}
            ],
            'isError': true,
          },
        };
      }

      try {
        final data = await tool.handler(args);
        return {
          'jsonrpc': '2.0',
          'id': id,
          'result': {
            'content': [
              {'type': 'text', 'text': jsonEncode(data)}
            ],
          },
        };
      } catch (e) {
        return {
          'jsonrpc': '2.0',
          'id': id,
          'result': {
            'content': [
              {'type': 'text', 'text': 'Error: $e'}
            ],
            'isError': true,
          },
        };
      }

    default:
      if (id == null) return null;
      return {
        'jsonrpc': '2.0',
        'id': id,
        'error': {'code': -32601, 'message': 'Method not found: $method'},
      };
  }
}

# kiwoom_rest_api

[![pub.dev](https://img.shields.io/pub/v/kiwoom_rest_api)](https://pub.dev/packages/kiwoom_rest_api)
[![GitHub](https://img.shields.io/github/license/KKimj/Kiwoom-REST-API)](https://github.com/KKimj/Kiwoom-REST-API)
[![CI](https://github.com/KKimj/Kiwoom-REST-API/actions/workflows/lint.yml/badge.svg)](https://github.com/KKimj/Kiwoom-REST-API/actions/workflows/lint.yml)

키움증권 REST OpenAPI Dart 클라이언트 라이브러리 + MCP 서버.

## MCP 서버 설치

```bash
dart pub global activate kiwoom_rest_api
```

`~/.mcp.json` 또는 Claude Desktop 설정:

```json
{
  "mcpServers": {
    "kiwoom": {
      "command": "kiwoom-rest-api",
      "env": {
        "KIWOOM_ENV": "live",
        "KIWOOM_APP_KEY": "YOUR_APP_KEY",
        "KIWOOM_APP_SECRET": "YOUR_APP_SECRET"
      }
    }
  }
}
```

> TypeScript 버전: `npx -y kiwoom-rest-api`

## 라이브러리 사용

```yaml
dependencies:
  kiwoom_rest_api: ^0.1.0
```

```dart
import 'package:kiwoom_rest_api/kiwoom_rest_api.dart';

final client = KiwoomClient(
  appKey: 'YOUR_APP_KEY',
  appSecret: 'YOUR_APP_SECRET',
  env: KiwoomEnv.live,
);

final result = await client.acnt.call('ka00001');
```

## 라이선스

MPL-2.0

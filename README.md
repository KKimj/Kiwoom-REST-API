# Kiwoom REST API

[![npm](https://img.shields.io/npm/v/kiwoom-rest-api)](https://www.npmjs.com/package/kiwoom-rest-api)
[![pub.dev](https://img.shields.io/pub/v/kiwoom_rest_api)](https://pub.dev/packages/kiwoom_rest_api)
[![CI](https://github.com/KKimj/Kiwoom-REST-API/actions/workflows/lint.yml/badge.svg)](https://github.com/KKimj/Kiwoom-REST-API/actions/workflows/lint.yml)
[![License: MPL-2.0](https://img.shields.io/badge/License-MPL_2.0-blue.svg)](LICENSE)

키움증권 REST OpenAPI 클라이언트 라이브러리 + MCP 서버. TypeScript와 Dart 두 가지 언어로 제공됩니다.

## MCP 서버 설치

Claude Desktop / Claude Code 등 MCP 클라이언트에 바로 연결할 수 있습니다.

**TypeScript (Node.js)**
```json
{
  "mcpServers": {
    "kiwoom": {
      "command": "npx",
      "args": ["-y", "kiwoom-rest-api"],
      "env": {
        "KIWOOM_ENV": "live",
        "KIWOOM_APP_KEY": "YOUR_APP_KEY",
        "KIWOOM_APP_SECRET": "YOUR_APP_SECRET"
      }
    }
  }
}
```

**Dart**
```bash
dart pub global activate kiwoom_rest_api
```
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

`KIWOOM_ENV`를 `mock`으로 설정하면 모의투자 API(`mockapi.kiwoom.com`)를 사용합니다.

## 라이브러리 사용

**TypeScript**
```bash
npm install kiwoom-rest-api
```
```typescript
import { KiwoomClient } from 'kiwoom-rest-api';

const client = new KiwoomClient({ appKey: '...', appSecret: '...', env: 'live' });
const result = await client.acnt.call('ka00001');
```

**Dart**
```yaml
dependencies:
  kiwoom_rest_api: ^0.1.0
```
```dart
import 'package:kiwoom_rest_api/kiwoom_rest_api.dart';

final client = KiwoomClient(appKey: '...', appSecret: '...', env: KiwoomEnv.live);
final result = await client.acnt.call('ka00001');
```

## 패키지

| 언어 | 패키지 | 경로 |
|---|---|---|
| TypeScript | [kiwoom-rest-api](https://www.npmjs.com/package/kiwoom-rest-api) | [`packages/typescript/`](packages/typescript/) |
| Dart | [kiwoom_rest_api](https://pub.dev/packages/kiwoom_rest_api) | [`packages/dart/`](packages/dart/) |

## 라이선스

MPL-2.0

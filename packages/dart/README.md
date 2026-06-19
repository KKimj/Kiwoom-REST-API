# kiwoom_rest_api

키움증권 REST OpenAPI Dart 클라이언트 라이브러리 + MCP 서버.

## 설치

```yaml
dependencies:
  kiwoom_rest_api: ^0.1.0
```

## 라이브러리 사용

```dart
import 'package:kiwoom_rest_api/kiwoom_rest_api.dart';

final client = KiwoomClient(
  appKey: 'YOUR_APP_KEY',
  appSecret: 'YOUR_APP_SECRET',
  env: KiwoomEnv.live,
);

final result = await client.acnt.call('ka00001');
```

## MCP 서버 실행

```bash
dart pub global activate kiwoom_rest_api

KIWOOM_ENV=live \
KIWOOM_APP_KEY=... \
KIWOOM_APP_SECRET=... \
kiwoom-rest-api
```

또는 `npx -y kiwoom-rest-api` (TypeScript 버전).

## 라이선스

MPL-2.0

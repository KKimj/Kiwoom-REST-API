# kiwoom-rest-api

MCP server for [Kiwoom Securities](https://www.kiwoom.com) REST API.  
182 tools covering trading, market data, account management, and more — auto-generated from the [official Kiwoom developer portal](https://openapi.kiwoom.com).

## Setup

**Step 1 — Get API credentials**

Sign up at [Kiwoom OpenAPI portal](https://openapi.kiwoom.com) → My Page → API Application.  
Obtain `app_key` and `secret_key`, and register your IP under IP Management.

**Step 2 — Add to MCP config**

```jsonc
// Claude Desktop: ~/Library/Application Support/Claude/claude_desktop_config.json
// Claude Code: ~/.mcp.json
{
  "mcpServers": {
    "kiwoom-rest-api-mock": {
      "command": "npx",
      "args": ["-y", "kiwoom-rest-api"],
      "env": {
        "KIWOOM_APP_KEY": "<your app_key>",
        "KIWOOM_APP_SECRET": "<your secret_key>",
        "KIWOOM_ENV": "mock"
      }
    },
    "kiwoom-rest-api-live": {
      "command": "npx",
      "args": ["-y", "kiwoom-rest-api"],
      "env": {
        "KIWOOM_APP_KEY": "<your app_key>",
        "KIWOOM_APP_SECRET": "<your secret_key>",
        "KIWOOM_ENV": "live"
      }
    }
  }
}
```

Register both `mock` and `live` simultaneously — your AI client can then explicitly choose which environment to call.

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `KIWOOM_APP_KEY` | ✓ | App key from Kiwoom portal |
| `KIWOOM_APP_SECRET` | ✓ | Secret key from Kiwoom portal |
| `KIWOOM_ENV` | — | `live` \| `mock` (default: `mock`) |
| `KIWOOM_ACCESS_TOKEN` | — | Provide token directly; skips auto-issuance |

Token lifecycle is managed automatically: issued on first call, refreshed 5 minutes before expiry.

## Tool naming

Tools follow the pattern `kiwoom_{segment}_{api_id}`:

| Segment | Category |
|---|---|
| `acnt` | 계좌 (Account) |
| `ordr` | 주문 (Order) |
| `stkinfo` | 종목정보 (Stock info) |
| `chart` | 차트 (Chart) |
| `mrkcond` | 시장상황 (Market condition) |
| `etf` | ETF |
| `elw` | ELW |
| `crdordr` | 신용주문 (Credit order) |
| `frgnistt` | 외국인기관 (Foreign/institutional) |
| `rkinfo` | 순위정보 (Ranking) |
| `sect` | 업종 (Sector) |
| `shsa` | 해외주식 (Overseas stock) |
| `slb` | 대차 (Securities lending) |
| `thme` | 테마 (Theme) |

Example: `kiwoom_acnt_ka00001` → 계좌번호조회

## License

[MPL-2.0](https://www.mozilla.org/en-US/MPL/2.0/)

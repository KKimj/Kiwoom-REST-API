# Changelog

## [0.2.1] - 2026-06-19
### fix
- remove deprecated API ka10009 (주식기관요청)

## [0.2.0] - 2026-06-19
### feat
- KiwoomClient library export
- dual entrypoint: library (index.js) + MCP server (cli.js)

### fix
- correct OAuth token endpoint (/oauth2/token)
- fix request field secretkey, response field token

### chore
- ESLint strictTypeChecked + Prettier

## [0.1.0] - 2026-06-10
### feat
- initial MCP server with 182 tools

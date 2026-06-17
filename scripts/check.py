#!/usr/bin/env python3
"""
openapi.json vs 키움 공식 포털 diff → GitHub Issue 자동 등록

Usage:
    python scripts/check.py
Env:
    GH_TOKEN  — GitHub 토큰 (Actions: secrets.GITHUB_TOKEN)
    GH_REPO   — owner/repo (Actions: github.repository)
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import requests

AJAX_URL = "https://openapi.kiwoom.com/guide/getApiInfoListAjax"
OPENAPI_PATH = Path(__file__).parent.parent / "openapi.json"


def fetch_official() -> dict[str, dict]:
    resp = requests.post(AJAX_URL, json={}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("resp_code") != "0":
        sys.exit(f"API 오류: {data.get('resp_msg')}")

    result = {}
    for entry in data["resp_data"]:
        api_id = entry.get("apiId", "").strip()
        if not api_id:
            continue
        info = entry.get("apiInfo", {})
        fields = entry.get("apiTrIo", [])
        result[api_id] = {
            "name": info.get("apiNm", api_id),
            "path": f"{info.get('svcUri','')}/{api_id}",
            "method": (info.get("jobMethod") or "POST").upper(),
            "input_fields": sorted(
                f["itemId"] for f in fields
                if f.get("inptOutputTp") == "I" and f.get("itemId")
            ),
            "output_fields": sorted(
                f["itemId"] for f in fields
                if f.get("inptOutputTp") == "O" and f.get("itemId")
            ),
        }
    return result


def load_spec() -> dict[str, dict]:
    if not OPENAPI_PATH.exists():
        sys.exit(f"{OPENAPI_PATH} 없음. generate_openapi.py 먼저 실행하세요.")
    with open(OPENAPI_PATH, encoding="utf-8") as f:
        spec = json.load(f)

    result = {}
    for path, methods in spec.get("paths", {}).items():
        for method, op in methods.items():
            api_id = op.get("x-api-id") or op.get("operationId", "")
            if not api_id:
                continue
            req_props = (
                op.get("requestBody", {})
                .get("content", {})
                .get("application/json", {})
                .get("schema", {})
                .get("properties", {})
            )
            res_props = (
                op.get("responses", {})
                .get("200", {})
                .get("content", {})
                .get("application/json", {})
                .get("schema", {})
                .get("properties", {})
            )
            result[api_id] = {
                "name": op.get("summary", api_id),
                "path": path,
                "method": method.upper(),
                "input_fields": sorted(req_props.keys()),
                "output_fields": sorted(res_props.keys()),
            }
    return result


def build_issue_body(new_apis, removed_apis, changed_fields, today: str) -> str:
    lines = [f"## 🔔 API Spec Drift — {today}\n"]
    lines.append("키움 공식 포털과 `openapi.json` 간 차이가 감지되었습니다.\n")

    lines.append("### ➕ 신규 API (공식 추가, spec 미반영)")
    if new_apis:
        lines.append("| API ID | 경로 | 설명 |")
        lines.append("|---|---|---|")
        for api_id, info in sorted(new_apis.items()):
            lines.append(f"| `{api_id}` | `{info['method']} {info['path']}` | {info['name']} |")
    else:
        lines.append("없음")

    lines.append("\n### ➖ 삭제된 API (공식 제거, spec 잔존)")
    if removed_apis:
        lines.append("| API ID | 경로 | 설명 |")
        lines.append("|---|---|---|")
        for api_id, info in sorted(removed_apis.items()):
            lines.append(f"| `{api_id}` | `{info['method']} {info['path']}` | {info['name']} |")
    else:
        lines.append("없음")

    lines.append("\n### 🔄 필드 변경")
    if changed_fields:
        lines.append("| API ID | 필드 | 변경 |")
        lines.append("|---|---|---|")
        for api_id, changes in sorted(changed_fields.items()):
            for change in changes:
                lines.append(f"| `{api_id}` | `{change['field']}` | {change['change']} |")
    else:
        lines.append("없음")

    lines.append("\n---")
    lines.append("`openapi.json` 업데이트: `python scripts/generate_openapi.py` 실행 후 PR.")
    return "\n".join(lines)


def has_open_drift_issue(repo: str, token: str) -> bool:
    result = subprocess.run(
        ["gh", "issue", "list", "-R", repo, "--state", "open",
         "--search", "API Spec Drift", "--json", "title"],
        capture_output=True, text=True,
        env={**os.environ, "GH_TOKEN": token},
    )
    if result.returncode != 0:
        return False
    issues = json.loads(result.stdout or "[]")
    return any("API Spec Drift" in i.get("title", "") for i in issues)


def create_issue(repo: str, token: str, title: str, body: str):
    result = subprocess.run(
        ["gh", "issue", "create", "-R", repo,
         "--title", title,
         "--body", body,
         "--label", "P1,api-drift"],
        capture_output=True, text=True,
        env={**os.environ, "GH_TOKEN": token},
    )
    if result.returncode != 0:
        # 라벨 없으면 먼저 생성
        for label, color, desc in [
            ("P1", "d93f0b", "Priority 1"),
            ("api-drift", "0075ca", "API spec drift detected"),
        ]:
            subprocess.run(
                ["gh", "label", "create", label, "-R", repo,
                 "--color", color, "--description", desc, "--force"],
                capture_output=True,
                env={**os.environ, "GH_TOKEN": token},
            )
        result = subprocess.run(
            ["gh", "issue", "create", "-R", repo,
             "--title", title,
             "--body", body,
             "--label", "P1,api-drift"],
            capture_output=True, text=True,
            env={**os.environ, "GH_TOKEN": token},
        )
    print(result.stdout.strip())
    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        sys.exit(1)


def diff_spec(official: dict, spec: dict) -> tuple[dict, dict, dict]:
    official_ids = set(official)
    spec_ids = set(spec)
    new_apis = {k: official[k] for k in official_ids - spec_ids}
    removed_apis = {k: spec[k] for k in spec_ids - official_ids}
    changed_fields: dict[str, list] = {}
    for api_id in official_ids & spec_ids:
        changes = []
        for field in set(official[api_id]["input_fields"]) - set(spec[api_id]["input_fields"]):
            changes.append({"field": field, "change": "입력 필드 추가됨"})
        for field in set(spec[api_id]["input_fields"]) - set(official[api_id]["input_fields"]):
            changes.append({"field": field, "change": "입력 필드 삭제됨"})
        for field in set(official[api_id]["output_fields"]) - set(spec[api_id]["output_fields"]):
            changes.append({"field": field, "change": "출력 필드 추가됨"})
        for field in set(spec[api_id]["output_fields"]) - set(official[api_id]["output_fields"]):
            changes.append({"field": field, "change": "출력 필드 삭제됨"})
        if changes:
            changed_fields[api_id] = changes
    return new_apis, removed_apis, changed_fields


def print_summary(official: dict, spec: dict, new_apis: dict, removed_apis: dict, changed_fields: dict) -> None:
    print(f"  공식 포털: {len(official)}개  /  openapi.json: {len(spec)}개")
    if new_apis:
        print(f"  ➕ 신규 {len(new_apis)}개: {', '.join(sorted(new_apis)[:5])}{'...' if len(new_apis) > 5 else ''}")
    if removed_apis:
        print(f"  ➖ 삭제 {len(removed_apis)}개: {', '.join(sorted(removed_apis)[:5])}{'...' if len(removed_apis) > 5 else ''}")
    if changed_fields:
        print(f"  🔄 필드변경 {len(changed_fields)}개: {', '.join(sorted(changed_fields)[:5])}{'...' if len(changed_fields) > 5 else ''}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ci",
        action="store_true",
        help="PR/머지 게이트 모드: drift 있으면 exit 1, Issue 미생성",
    )
    args = parser.parse_args()

    today = str(date.today())

    print("공식 포털 조회 중...", file=sys.stderr)
    official = fetch_official()
    print("openapi.json 로드 중...", file=sys.stderr)
    spec = load_spec()

    new_apis, removed_apis, changed_fields = diff_spec(official, spec)

    if not new_apis and not removed_apis and not changed_fields:
        print(f"✅ No drift — 공식 포털({len(official)}개) = openapi.json({len(spec)}개), 모든 필드 일치")
        sys.exit(0)

    print("⚠️  Drift 감지:")
    print_summary(official, spec, new_apis, removed_apis, changed_fields)

    if args.ci:
        sys.exit(1)

    token = os.environ.get("GH_TOKEN", "")
    repo = os.environ.get("GH_REPO", "")
    if not token or not repo:
        print("GH_TOKEN / GH_REPO 미설정 — Issue 등록 건너뜀.")
        sys.exit(1)

    if has_open_drift_issue(repo, token):
        print("이미 열려있는 Drift Issue가 있습니다 — 중복 등록 건너뜀.")
        sys.exit(1)

    title = f"API Spec Drift: {today}"
    body = build_issue_body(new_apis, removed_apis, changed_fields, today)
    create_issue(repo, token, title, body)
    print(f"Issue 생성 완료: {title}")
    sys.exit(1)


if __name__ == "__main__":
    main()

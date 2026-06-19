#!/usr/bin/env python3
"""
openapi.json vs 키움 공식 포털 diff → 드리프트 감지 시 자동 PR 생성

Usage:
    python scripts/check.py
Env:
    GH_TOKEN  — GitHub 토큰 (Actions: secrets.GITHUB_TOKEN)
    GH_REPO   — owner/repo (Actions: github.repository)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import requests

AJAX_URL = "https://openapi.kiwoom.com/guide/getApiInfoListAjax"
REPO_ROOT = Path(__file__).parent.parent
OPENAPI_PATH = REPO_ROOT / "openapi.json"


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
            "path": f"{info.get('svcUri', '')}/{api_id}",
            "method": (info.get("jobMethod") or "POST").upper(),
            "input_fields": sorted(
                f["itemId"] for f in fields if f.get("inptOutputTp") == "I" and f.get("itemId")
            ),
            "output_fields": sorted(
                f["itemId"] for f in fields if f.get("inptOutputTp") == "O" and f.get("itemId")
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


def print_summary(
    official: dict, spec: dict, new_apis: dict, removed_apis: dict, changed_fields: dict
) -> None:
    print(f"  공식 포털: {len(official)}개  /  openapi.json: {len(spec)}개")
    if new_apis:
        print(
            f"  ➕ 신규 {len(new_apis)}개: {', '.join(sorted(new_apis)[:5])}{'...' if len(new_apis) > 5 else ''}"
        )
    if removed_apis:
        print(
            f"  ➖ 삭제 {len(removed_apis)}개: {', '.join(sorted(removed_apis)[:5])}{'...' if len(removed_apis) > 5 else ''}"
        )
    if changed_fields:
        print(
            f"  🔄 필드변경 {len(changed_fields)}개: {', '.join(sorted(changed_fields)[:5])}{'...' if len(changed_fields) > 5 else ''}"
        )


# ── 자동화 헬퍼 ────────────────────────────────────────────────────────────────

def bump_patch(version: str) -> str:
    parts = version.split(".")
    parts[-1] = str(int(parts[-1]) + 1)
    return ".".join(parts)


def get_current_ts_version() -> str:
    pkg = json.loads((REPO_ROOT / "packages/typescript/package.json").read_text())
    return pkg["version"]


def get_current_dart_version() -> str:
    text = (REPO_ROOT / "packages/dart/pubspec.yaml").read_text()
    m = re.search(r"^version:\s*(.+)$", text, re.MULTILINE)
    return m.group(1).strip() if m else "0.0.0"


def bump_ts_version(new_ver: str) -> None:
    path = REPO_ROOT / "packages/typescript/package.json"
    pkg = json.loads(path.read_text())
    pkg["version"] = new_ver
    path.write_text(json.dumps(pkg, indent=2, ensure_ascii=False) + "\n")


def bump_dart_version(new_ver: str) -> None:
    path = REPO_ROOT / "packages/dart/pubspec.yaml"
    text = path.read_text()
    text = re.sub(r"^version: .+$", f"version: {new_ver}", text, flags=re.MULTILINE)
    path.write_text(text)


def prepend_changelog(path: Path, version: str, date_str: str, body: str) -> None:
    existing = path.read_text() if path.exists() else "# Changelog\n"
    entry = f"\n## [{version}] - {date_str}\n{body}\n"
    if "# Changelog\n" in existing:
        new = existing.replace("# Changelog\n", f"# Changelog\n{entry}", 1)
    else:
        new = f"# Changelog\n{entry}\n{existing}"
    path.write_text(new)


def run_cmd(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, cwd=REPO_ROOT)


def build_changelog_body(new_apis: dict, removed_apis: dict, changed_fields: dict) -> str:
    lines = []
    if removed_apis:
        lines.append("### fix")
        for api_id, info in sorted(removed_apis.items()):
            lines.append(f"- remove deprecated API `{api_id}` ({info['name']})")
    if new_apis:
        lines.append("### feat")
        for api_id, info in sorted(new_apis.items()):
            lines.append(f"- add new API `{api_id}` ({info['name']})")
    if changed_fields:
        if not removed_apis:
            lines.append("### fix")
        for api_id, changes in sorted(changed_fields.items()):
            lines.append(f"- update fields for `{api_id}` ({len(changes)} changes)")
    return "\n".join(lines)


def build_pr_body(
    new_apis: dict, removed_apis: dict, changed_fields: dict,
    today: str, cur_ts: str, new_ts: str, cur_dart: str, new_dart: str,
) -> str:
    lines = [
        f"## Auto-generated API spec update — {today}",
        "",
        "키움 공식 포털과 `openapi.json` 간 차이가 감지되어 자동 갱신합니다.",
        "",
        f"- TypeScript: `{cur_ts}` → `{new_ts}`",
        f"- Dart: `{cur_dart}` → `{new_dart}`",
        "",
    ]
    if removed_apis:
        lines.append("### ➖ 삭제된 API")
        lines.append("| API ID | 설명 |")
        lines.append("|---|---|")
        for api_id, info in sorted(removed_apis.items()):
            lines.append(f"| `{api_id}` | {info['name']} |")
        lines.append("")
    if new_apis:
        lines.append("### ➕ 신규 API")
        lines.append("| API ID | 경로 | 설명 |")
        lines.append("|---|---|---|")
        for api_id, info in sorted(new_apis.items()):
            lines.append(f"| `{api_id}` | `{info['method']} {info['path']}` | {info['name']} |")
        lines.append("")
    if changed_fields:
        lines.append("### 🔄 필드 변경")
        lines.append("| API ID | 필드 | 변경 |")
        lines.append("|---|---|---|")
        for api_id, changes in sorted(changed_fields.items()):
            for change in changes:
                lines.append(f"| `{api_id}` | `{change['field']}` | {change['change']} |")
        lines.append("")
    lines.append("---")
    lines.append("*이 PR은 `scripts/check.py`가 자동 생성했습니다.*")
    return "\n".join(lines)


def create_auto_pr(
    new_apis: dict, removed_apis: dict, changed_fields: dict,
    today: str, token: str, repo: str,
) -> None:
    branch = f"fix/auto-drift-{today}"
    env = {**os.environ, "GH_TOKEN": token}

    # git 설정
    subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"],
                   check=True, cwd=REPO_ROOT)
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"],
                   check=True, cwd=REPO_ROOT)

    # 원격 URL에 토큰 삽입 (Actions 환경 push 권한)
    remote_url = subprocess.check_output(
        ["git", "remote", "get-url", "origin"], cwd=REPO_ROOT, text=True
    ).strip()
    if remote_url.startswith("https://") and "@" not in remote_url:
        authed = remote_url.replace("https://", f"https://x-access-token:{token}@")
        subprocess.run(["git", "remote", "set-url", "origin", authed],
                       check=True, cwd=REPO_ROOT)

    # 브랜치
    subprocess.run(["git", "checkout", "-b", branch], check=True, cwd=REPO_ROOT)

    # 1. openapi.json 재생성
    print("generate_openapi.py 실행 중...", file=sys.stderr)
    run_cmd(["python3", "scripts/generate_openapi.py"])

    # 2. 패키지 재생성
    print("TypeScript 패키지 재생성 중...", file=sys.stderr)
    run_cmd(["python3", "build/typescript/generate.py"])
    print("Dart 패키지 재생성 중...", file=sys.stderr)
    run_cmd(["python3", "build/dart/generate.py"])

    # 3. 버전 bump
    cur_ts = get_current_ts_version()
    new_ts = bump_patch(cur_ts)
    cur_dart = get_current_dart_version()
    new_dart = bump_patch(cur_dart)
    bump_ts_version(new_ts)
    bump_dart_version(new_dart)

    # 4. CHANGELOG prepend
    changelog_body = build_changelog_body(new_apis, removed_apis, changed_fields)
    for cl_path in [
        REPO_ROOT / "CHANGELOG.md",
        REPO_ROOT / "packages/typescript/CHANGELOG.md",
        REPO_ROOT / "packages/dart/CHANGELOG.md",
    ]:
        prepend_changelog(cl_path, new_ts, today, changelog_body)

    # 5. 커밋 & 푸시
    subprocess.run(["git", "add", "-A"], check=True, cwd=REPO_ROOT)
    commit_msg = (
        f"fix: auto-update API spec {today}\n\n"
        f"Drift detected — regenerated openapi.json, TS/Dart packages.\n"
        f"TypeScript: {cur_ts} → {new_ts} / Dart: {cur_dart} → {new_dart}"
    )
    subprocess.run(["git", "commit", "-m", commit_msg], check=True, cwd=REPO_ROOT)
    subprocess.run(["git", "push", "-u", "origin", branch], check=True, cwd=REPO_ROOT, env=env)

    # 6. PR 생성
    pr_body = build_pr_body(new_apis, removed_apis, changed_fields,
                            today, cur_ts, new_ts, cur_dart, new_dart)
    result = subprocess.run(
        [
            "gh", "pr", "create",
            "-R", repo,
            "--title", f"fix: auto-update API spec ({today})",
            "--body", pr_body,
            "--head", branch,
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    print(result.stdout.strip())
    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        sys.exit(1)


# ── main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="드리프트 있으면 exit 1, PR 미생성",
    )
    args = parser.parse_args()

    today = str(date.today())

    print("공식 포털 조회 중...", file=sys.stderr)
    official = fetch_official()
    print("openapi.json 로드 중...", file=sys.stderr)
    spec = load_spec()

    new_apis, removed_apis, changed_fields = diff_spec(official, spec)

    if not new_apis and not removed_apis and not changed_fields:
        print(
            f"✅ No drift — 공식 포털({len(official)}개) = openapi.json({len(spec)}개), 모든 필드 일치"
        )
        sys.exit(0)

    print("⚠️  Drift 감지:")
    print_summary(official, spec, new_apis, removed_apis, changed_fields)

    if args.dry_run:
        sys.exit(1)

    token = os.environ.get("GH_TOKEN", "")
    repo = os.environ.get("GH_REPO", "")
    if not token or not repo:
        print("GH_TOKEN / GH_REPO 미설정 — PR 생성 건너뜀.")
        sys.exit(1)

    create_auto_pr(new_apis, removed_apis, changed_fields, today, token, repo)
    print("✅ PR 생성 완료")


if __name__ == "__main__":
    main()

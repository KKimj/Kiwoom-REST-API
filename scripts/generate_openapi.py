#!/usr/bin/env python3
"""
키움 REST API 공식 포털 AJAX → openapi.json 생성

Usage:
    python scripts/generate_openapi.py [--output openapi.json]
"""
import argparse
import contextlib
import json
import sys
from datetime import date
from pathlib import Path

import requests

AJAX_URL = "https://openapi.kiwoom.com/guide/getApiInfoListAjax"

COMMON_HEADERS = [
    {
        "name": "authorization",
        "in": "header",
        "required": True,
        "schema": {"type": "string"},
        "description": "Bearer {접근토큰}",
    },
    {
        "name": "api-id",
        "in": "header",
        "required": True,
        "schema": {"type": "string"},
        "description": "API ID (e.g. ka10001)",
    },
    {
        "name": "cont-yn",
        "in": "header",
        "required": False,
        "schema": {"type": "string", "enum": ["Y", "N"], "default": "N"},
        "description": "연속조회 여부",
    },
    {
        "name": "next-key",
        "in": "header",
        "required": False,
        "schema": {"type": "string"},
        "description": "연속조회 키",
    },
]


def fetch_official() -> list[dict]:
    resp = requests.post(AJAX_URL, json={}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("resp_code") != "0":
        sys.exit(f"API 오류: {data.get('resp_msg')}")
    return data["resp_data"]


def field_to_schema(field: dict) -> dict:
    t = (field.get("type") or "String").lower()
    if t in ("int", "integer", "long"):
        return {"type": "integer"}
    if t in ("double", "float", "number"):
        return {"type": "number"}
    return {"type": "string"}


def build_properties(fields: list[dict]) -> dict:
    props = {}
    for f in fields:
        item_id = f.get("itemId", "").strip()
        if not item_id:
            continue
        schema = field_to_schema(f)
        desc_parts = []
        if f.get("itemNm"):
            desc_parts.append(f["itemNm"])
        if f.get("itemDc"):
            desc_parts.append(f["itemDc"])
        if f.get("sampData"):
            desc_parts.append(f"예: {f['sampData']}")
        if desc_parts:
            schema["description"] = " / ".join(desc_parts)
        if f.get("lngt"):
            with contextlib.suppress(ValueError, TypeError):
                schema["maxLength"] = int(f["lngt"])
        props[item_id] = schema
    return props


def build_required(fields: list[dict]) -> list[str]:
    return [f["itemId"] for f in fields if f.get("esntYn") == "Y" and f.get("itemId")]


def api_to_path(entry: dict) -> tuple[str, str, dict]:
    info = entry.get("apiInfo", {})
    api_id = entry.get("apiId", "").strip()
    if not api_id:
        raise ValueError("apiId가 비어 있습니다.")
    svc_uri = (info.get("svcUri") or "").rstrip("/")
    method = (info.get("jobMethod") or "POST").lower()
    api_name = (info.get("apiNm") or api_id)

    path = f"{svc_uri}/{api_id}"

    fields = entry.get("apiTrIo", [])

    req_body_fields = [
        f for f in fields
        if f.get("inptOutputTp") == "I" and f.get("headBodyTp") == "B"
    ]
    req_header_fields = [
        f for f in fields
        if f.get("inptOutputTp") == "I" and f.get("headBodyTp") == "H"
    ]
    res_fields = [f for f in fields if f.get("inptOutputTp") == "O"]

    operation: dict = {
        "operationId": api_id,
        "summary": api_name,
        "x-api-id": api_id,
        "x-real-path": svc_uri,
        "parameters": [{"$ref": f"#/components/parameters/{p['name']}"} for p in COMMON_HEADERS],
        "responses": {
            "200": {
                "description": "성공",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": build_properties(res_fields),
                        }
                    }
                },
            }
        },
    }

    # extra header parameters not in common
    common_ids = {"authorization", "api-id", "cont-yn", "next-key"}
    for hf in req_header_fields:
        item_id = hf.get("itemId", "").strip()
        if item_id and item_id.lower() not in common_ids:
            operation["parameters"].append({
                "name": item_id,
                "in": "header",
                "required": hf.get("esntYn") == "Y",
                "schema": field_to_schema(hf),
                "description": hf.get("itemNm", ""),
            })

    if req_body_fields:
        props = build_properties(req_body_fields)
        req = build_required(req_body_fields)
        body_schema: dict = {"type": "object", "properties": props}
        if req:
            body_schema["required"] = req
        operation["requestBody"] = {
            "required": True,
            "content": {"application/json": {"schema": body_schema}},
        }

    # tags: "{segment} / {grpCodeNm}" 병기
    grp = (info.get("grpCodeNm") or "").strip()
    parts = [p for p in svc_uri.strip("/").split("/") if p and p not in ("api",)]
    segment = parts[-1] if parts else ""
    if segment and grp:
        tag = f"{segment} / {grp}"
    elif grp:
        tag = grp
    elif segment:
        tag = segment
    else:
        tag = "기타"
    operation["tags"] = [tag]

    return path, method, operation


def build_spec(entries: list[dict]) -> dict:
    paths: dict = {}
    for entry in entries:
        try:
            path, method, operation = api_to_path(entry)
        except Exception as e:
            print(f"  skip {entry.get('apiId')}: {e}", file=sys.stderr)
            continue
        if path not in paths:
            paths[path] = {}
        paths[path][method] = operation

    components_params = {p["name"]: {**p} for p in COMMON_HEADERS}

    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Kiwoom REST API",
            "version": str(date.today()),
            "description": (
                "키움증권 REST API (https://openapi.kiwoom.com)\n\n"
                "이 파일은 공식 포털 AJAX에서 자동 생성됩니다. "
                "직접 수정하지 마세요 — `python scripts/generate_openapi.py`로 재생성하세요.\n\n"
                "**실제 API 경로**: 각 operation의 `x-real-path` 참고. "
                "path의 마지막 세그먼트(apiId)는 문서화 목적 구분자이며, "
                "실제 호출 시 `api-id` 헤더로 전달합니다."
            ),
            "license": {
                "name": "Mozilla Public License 2.0",
                "url": "https://www.mozilla.org/en-US/MPL/2.0/",
            },
            "contact": {
                "url": "https://github.com/KKimj/Kiwoom-REST-API",
            },
        },
        "servers": [
            {"url": "https://api.kiwoom.com", "description": "실거래"},
            {"url": "https://mockapi.kiwoom.com", "description": "모의투자"},
        ],
        "paths": paths,
        "components": {
            "parameters": components_params,
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "description": "/oauth2/token/au10001 로 발급한 접근토큰",
                }
            },
        },
        "security": [{"bearerAuth": []}],
    }


def write_spec(spec: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  → {path} 저장 완료", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="openapi.json")
    parser.add_argument("--no-docs", action="store_true", help="docs/openapi.json 미생성")
    args = parser.parse_args()

    print("공식 포털에서 API 목록 조회 중...", file=sys.stderr)
    entries = fetch_official()
    print(f"  → {len(entries)}개 API 수신", file=sys.stderr)

    spec = build_spec(entries)
    print(f"  → {len(spec['paths'])}개 경로 생성", file=sys.stderr)

    out = Path(args.output)
    write_spec(spec, out)

    if not args.no_docs:
        docs_out = out.parent / "docs" / "openapi.json"
        if docs_out != out:
            write_spec(spec, docs_out)


if __name__ == "__main__":
    main()

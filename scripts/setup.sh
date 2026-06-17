#!/bin/sh
# 로컬 개발 환경 초기 설정 — 클론 후 1회 실행
chmod +x .githooks/pre-commit .githooks/pre-push
git config core.hooksPath .githooks
echo "✅  git hooks 설치 및 권한 설정 완료 (.githooks/)"

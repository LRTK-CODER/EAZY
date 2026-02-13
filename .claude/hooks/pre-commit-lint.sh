#!/bin/bash
# Claude Code PreToolUse hook: git commit 전 staged .py 파일에 ruff 실행
# pre-commit hook이 파일을 수정하는 것을 방지하여 "외부 변경" 감지 문제 해결

INPUT=$(cat)

# jq 우선, 없으면 python3 fallback
if command -v jq &>/dev/null; then
  COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
else
  COMMAND=$(echo "$INPUT" | python3 -c \
    "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" \
    2>/dev/null || true)
fi

# git commit 명령이 아니면 무시
if ! echo "$COMMAND" | grep -q 'git commit'; then
  exit 0
fi

# staged .py 파일 목록
STAGED_PY=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null | grep '\.py$' || true)

if [[ -z "$STAGED_PY" ]]; then
  exit 0
fi

# ruff 실행 (lint fix + format)
for f in $STAGED_PY; do
  if [[ -f "$f" ]]; then
    uv run ruff check --fix "$f" 2>/dev/null || true
    uv run ruff format "$f" 2>/dev/null || true
  fi
done

# 수정된 파일 재-staging
echo "$STAGED_PY" | xargs git add 2>/dev/null || true

exit 0

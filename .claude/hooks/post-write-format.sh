#!/bin/bash
# Claude Code PostToolUse hook: Write 도구로 .py 파일 생성/수정 후 자동 ruff format
# Write 직후 포맷을 맞춰서 이후 ruff format --check 실패를 방지

INPUT=$(cat)

# file_path 추출
if command -v jq &>/dev/null; then
  FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
else
  FILE_PATH=$(echo "$INPUT" | python3 -c \
    "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" \
    2>/dev/null || true)
fi

# .py 파일이 아니면 무시
if [[ "$FILE_PATH" != *.py ]]; then
  exit 0
fi

# 파일 존재 확인
if [[ ! -f "$FILE_PATH" ]]; then
  exit 0
fi

# ruff lint fix + format 실행
uv run ruff check --fix "$FILE_PATH" 2>/dev/null || true
uv run ruff format "$FILE_PATH" 2>/dev/null || true

exit 0

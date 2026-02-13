#!/bin/bash
# Claude Code PostToolUse hook: 구현 커밋 후 TASK.md 업데이트 리마인드
# git commit이 feat/fix/test/refactor 접두사이면 TASK.md 업데이트 + 검증을 안내

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

# 직전 커밋 메시지 확인
LAST_MSG=$(git log -1 --pretty=%s 2>/dev/null)

# 구현 커밋(feat, fix, test, refactor)인지 확인
if ! echo "$LAST_MSG" | grep -qiE '^(feat|fix|test|refactor)'; then
  exit 0
fi

# TASK.md가 이 커밋에 포함되었으면 이미 업데이트됨 → 무시
if git diff-tree --no-commit-id --name-only -r HEAD 2>/dev/null | grep -q 'plan/TASK.md'; then
  exit 0
fi

# 리마인드 출력
cat <<'MSG'
📋 TASK.md 업데이트 리마인드: 구현 커밋이 완료되었습니다. 다음을 수행하세요:
1. plan/TASK.md 체크박스를 업데이트하세요 (완료된 Task/Quality Gate 체크)
2. 검증을 실행하세요:
   - uv run pytest tests/ -v
   - uv run pytest --cov=src/eazy/cli --cov-report=term-missing
   - uv run ruff check src/ tests/
3. TASK.md 변경사항을 커밋하세요 (docs: update TASK.md ...)
MSG

exit 0

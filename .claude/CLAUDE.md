# EAZY — 지침

## 규칙

`.claude/rules/`에 상세 규칙이 있다. 핵심만 요약:

- **검증 기준이 먼저:** SPEC의 검증 기준 → RED 테스트 → GREEN 구현 → REFACTOR
- **문서 먼저, 코드 나중:** 계획에 없는 것을 발견하면 코드 전에 문서를 업데이트
- **인터페이스 계약 준수:** Stage 간 데이터는 Pydantic BaseModel (dict 금지)
- **1 PR = 1 SPEC:** 여러 SPEC을 하나의 PR에 섞지 않는다
- **TDD 세션 격리:** RED/GREEN/REFACTOR 각각 별도 세션

상세:
- `coding-rules.md` — 코드 작성 규칙, Google 스타일 docstring, 금지 사항
- `commit-convention.md` — 커밋 메시지 형식
- `development-workflow.md` — 개발 프로세스, 문서 계층, Document-First 규칙
- `pr-rules.md` — PR 작성/머지/리뷰 규칙

## 작업 시작 전 확인

1. 지금 작업할 SPEC 번호를 확인한다
2. 해당 SPEC의 검증 기준을 읽는다
3. 해당 TASK의 현재 단계(RED/GREEN/REFACTOR)를 확인한다
4. SPEC에 없는 것은 구현하지 않는다 — 필요하면 SPEC을 먼저 업데이트한다

## 계획에 없는 것을 발견했을 때

1. 현재 작업 커밋 (진행 중 상태로)
2. `EAZY/DISCOVERIES.md`에 기록 - `docs/templates/DISCOVERIES.template.md` 양식을 따라 작성 필요
3. 크기 판단: 소(SPEC 내 해결) / 중(새 SPEC 필요) / 대(PRD 수준)
4. 소 → 즉시 처리, 중/대 → 현재 SPEC 완료 후 처리
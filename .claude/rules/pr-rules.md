# PR 작성 규칙

## PR 단위

- 1 PR = 1 SPEC (또는 1 SPEC 내 1 Feature)
- 여러 SPEC을 하나의 PR에 섞지 않는다
- 예외: SPEC-000(테스트 인프라)과 SPEC-001을 함께 올리는 초기 셋업

## PR 제목

```
[SPEC-NNN] <type>: <subject>
```

| type | 용도 |
|------|------|
| `feat` | 기능 구현 (TDD 사이클 포함) |
| `fix` | 버그 수정 |
| `refactor` | 동작 변경 없는 개선 |
| `docs` | 문서만 변경 |
| `plan` | SPEC/TASK 작성 |
| `infra` | 플러그인/Docker/CI |

```
# 좋은 예
[SPEC-001] feat: 세션 미들웨어 쿠키/JWT/CSRF 자동 관리
[SPEC-011] fix: 스캐너 타임아웃 시 나머지 플러그인 중단 방지
[SPEC-033] plan: L2 결과 통합기 검증 기준 + 인터페이스 계약

# 나쁜 예
세션 미들웨어 구현              ← SPEC 번호 없음
[SPEC-001] 수정                ← 무슨 수정인지 안 보임
[SPEC-001][SPEC-002] feat: ... ← 두 SPEC 섞임
```

## 머지 조건 (전부 충족해야 머지)

1. SPEC 검증 기준 전부 통과 (PR 본문 체크리스트 100%)
2. 전체 테스트 스위트 통과 (리그레션 없음)
3. 커버리지 80% 이상
4. `ruff check` + `mypy` 에러 0
5. SPEC 인터페이스 계약(Pydantic 모델) 준수
6. 인터페이스 변경 시 ARCHITECTURE.md 3절 동시 업데이트

## 브랜치 네이밍

```
spec-NNN/[간단한-설명]
```

```
spec-000/test-infra
spec-001/session-middleware
spec-011/parallel-scanner
spec-033/l2-result-merger
```

## PR 본문 필수 섹션

1. **관련 SPEC/TASK** — 어떤 SPEC의 어떤 TASK인지
2. **변경 요약** — 2~3문장으로 무엇을 왜
3. **SPEC 검증 기준 통과 현황** — 기준별 체크박스 + 테스트 함수 매핑
4. **테스트 결과** — pytest 실행 결과 붙여넣기
5. **품질 체크** — ruff, mypy, 커버리지
6. **인터페이스 영향** — 기존 모델 변경 여부
7. **개발 중 발견 사항** — 계획에 없던 발견 기록

## 인터페이스 변경이 있는 PR

ARCHITECTURE.md 3절의 Stage 간 인터페이스(Pydantic 모델)를 변경하면:

1. PR 본문 "인터페이스 영향"에 변경 내용 명시
2. ARCHITECTURE.md 3절 업데이트를 같은 PR에 포함
3. 영향받는 다른 SPEC 목록 명시
4. 필드 추가는 `| None` 기본값으로 역호환 유지
5. 필드 삭제/타입 변경은 PR 제목에 `BREAKING CHANGE` 표기

```
[SPEC-014] feat: BREAKING CHANGE — ReconOutput에 crypto_context 필수화
```

## 개발 중 발견 사항 처리

PR에서 계획에 없던 것을 발견했으면:

- 소(현재 SPEC 내 해결): 이 PR에서 SPEC 검증 기준 추가 + 테스트 추가 + 구현
- 중(새 SPEC 필요): 이 PR에 포함하지 않음. DISCOVERIES.md에 기록하고 별도 SPEC/PR로 분리
- 대(PRD 수준 변경): 이 PR에 포함하지 않음. PRD 논의 후 별도 진행

**"중/대" 발견을 현재 PR에 억지로 끼워넣지 않는다.** PR 스코프가 커지면 리뷰가 어려워지고 리그레션 위험이 증가한다.

## 문서 전용 PR

SPEC/TASK/ARCHITECTURE/PRD만 변경하는 PR도 허용한다:

```
[SPEC-033] plan: L2 결과 통합기 검증 기준 작성
```

- 코드 변경 없음
- 테스트 체크리스트 생략 가능
- 리뷰어는 검증 기준의 구체성과 인터페이스 계약 완성도를 확인

## 리뷰 체크리스트 (리뷰어용)

- [ ] SPEC 검증 기준과 테스트가 1:1 대응하는가
- [ ] 테스트가 public API만 검증하는가 (private 메서드 테스트 없음)
- [ ] Pydantic 모델이 SPEC 인터페이스 계약과 일치하는가
- [ ] SPEC에 없는 기능을 구현하지 않았는가
- [ ] 발견 사항이 적절한 크기로 분류되어 처리되었는가
- [ ] 커밋 메시지가 컨벤션을 따르는가 (`type(SPEC-NNN): subject`)
# 구현 계획: MVP 프론트엔드 (인덱스)

**상태**: ✅ Phase 5-Pre 완료 → ✅ Phase 5 Step 2 완료 → ✅ Phase 5 Step 3 완료 → 🔄 Phase 5-Improvements 계획 중
**시작일**: 2025-12-28
**최근 업데이트**: 2026-01-07 (Phase 5 Step 3: TargetList "View Results" 버튼 완료 - TDD GREEN 34/34 통과)
**예상 완료일**: 2026-01-12 (Phase 5-Pre: 3시간, Phase 5: 13시간, Phase 5-Improvements: 14-18시간, Phase 6: 5시간)

---

**⚠️ 중요 지침**: 각 Phase 완료 후 반드시:
1. ✅ 완료된 작업 체크박스를 체크
2. 🧪 모든 품질 게이트 검증 명령어 실행
3. ⚠️ 모든 품질 게이트 항목이 통과했는지 확인
4. 📅 위의 "최근 업데이트" 날짜 갱신
5. 📝 Notes 섹션에 학습 내용 문서화
6. ➡️ 그 후에만 다음 Phase로 진행

⛔ **품질 게이트를 건너뛰거나 실패한 체크를 무시하고 진행하지 말 것**

---

## 📋 개요

### 기능 설명
**React** (Vite), **TypeScript**, **TailwindCSS**, **shadcn/ui**를 사용하여 EAZY MVP 프론트엔드를 구축합니다.
프론트엔드는 프로젝트와 Target을 관리하고 스캔 결과를 확인할 수 있는 대시보드를 제공합니다.

### 성공 기준
- [x] Vite & TypeScript로 프로젝트가 성공적으로 초기화됨.
- [x] Shadcn/UI 컴포넌트가 구성되고 작동함.
- [x] 사용자가 UI를 통해 프로젝트와 Target을 생성/조회/수정/삭제할 수 있음.
- [x] 사용자가 스캔을 트리거하고 결과(Assets)를 확인할 수 있음.
- [x] **TDD**: Vitest & React Testing Library를 사용하여 컴포넌트 테스트 구현.

### 사용자 영향
- DAST 도구를 위한 그래픽 인터페이스를 제공하여 Raw API 호출을 대체.
- 공격 표면 데이터를 시각화하여 분석을 용이하게 함.

---

## 🏗️ 아키텍처 결정

| 결정 사항 | 근거 | 트레이드오프 |
|----------|------|------------|
| **Vite** | 빠른 빌드 시간, 최신 생태계. | - |
| **shadcn/ui** | 복사-붙여넣기 컴포넌트, 높은 커스터마이징, 접근성. | npm 패키지가 아니므로 수동 컴포넌트 관리 필요. |
| **Zustand** | 간단한 전역 상태 관리 (필요시). | Redux보다 보일러플레이트 적음. |
| **TanStack Query** | 서버 상태 관리 (API 캐시, 로딩 상태). | 단순한 앱에는 복잡도 증가하지만, 데이터 중심 대시보드에는 필수. |
| **Atomic Layout** | `components/ui` (atoms), `components/features` (molecules/organisms), `pages` (templates). | 재사용성과 작은 컴포넌트 크기 촉진. |

---

## 📦 의존성

### 시작 전 필수 요구사항
- 백엔드 API 실행 중 (통합을 위해)

### 외부 의존성
- `react`, `react-dom`, `react-router-dom`
- `axios` (또는 `ky` / `fetch`)
- `@tanstack/react-query`
- `tailwindcss`, `postcss`, `autoprefixer`
- `lucide-react` (아이콘)
- `clsx`, `tailwind-merge` (유틸)
- `zod`, `react-hook-form` (폼)
- **Dev**: `vitest`, `@testing-library/react`, `jsdom`

---

## 🧪 테스트 전략

### 테스트 접근 방식
**TDD (테스트 주도 개발)**:
1. **RED**: 실패하는 테스트를 먼저 작성 (예: "프로젝트 목록 렌더링").
2. **GREEN**: 테스트를 통과하는 컴포넌트 구현.
3. **REFACTOR**: 코드 구조 및 스타일 개선.

### 이 기능의 테스트 피라미드
| 테스트 유형 | 커버리지 목표 | 목적 |
|-----------|--------------|------|
| **Unit/Component** | ≥80% | UI 컴포넌트, 훅, 유틸 |
| **Integration** | 주요 흐름 | 페이지 수준 상호작용 (모킹된 API) |

---

## 📚 Phase별 문서 링크

| Phase | 상태 | 문서 | 예상 시간 | 완료율 | 테스트 |
|-------|------|------|-----------|--------|--------|
| **Phase 1-3** | ✅ 완료 | [PHASE1-3_COMPLETED.md](./PHASE1-3_COMPLETED.md) | 10h | 100% | 168/168 ✅ |
| **Phase 4** | ✅ 완료 | [PHASE4_COMPLETED.md](./PHASE4_COMPLETED.md) | 8h | 100% | 28/28 ✅ |
| **Phase 5** | ✅ 진행 | [PHASE5_CURRENT.md](./PHASE5_CURRENT.md) | 13h | 100% | 34/34 ✅ |
| **Phase 5-Improvements** | ⏳ 계획 | [PHASE5-IMPROVEMENTS.md](./PHASE5-IMPROVEMENTS.md) | 14-18h | 0% | - |
| **Phase 5.5-6** | ⏳ 미래 | [PHASE5.5-6_FUTURE.md](./PHASE5.5-6_FUTURE.md) | 8h | - | - |

---

## 📝 참고 문서

- **학습 내용 & 개발 이력**: [NOTES.md](./NOTES.md)
- **Backend MVP 계획**: [../PLAN_MVP_Backend.md](../PLAN_MVP_Backend.md)
- **전체 프로젝트 문서**: [../../.claude/CLAUDE.md](../../.claude/CLAUDE.md)

---

## 🎯 현재 작업

👉 **Phase 5-Improvements**: 크롤링 상태 개선, HTTP 패킷 조회, 파라미터 파싱
   - **예상 시작일**: 2026-01-08
   - **예상 소요 시간**: 14-18시간
   - **자세한 내용**: [PHASE5-IMPROVEMENTS.md](./PHASE5-IMPROVEMENTS.md)

### 진행 상황 요약

#### ✅ 완료된 Phase
- **Phase 1**: 프로젝트 초기화 & 인프라 (2h)
- **Phase 2**: 레이아웃 & 디자인 시스템 기반 (3h)
- **Phase 3**: 프로젝트 CRUD (사이드바) (5h) - **168개 테스트 통과**
- **Phase 4**: 프로젝트 상세 페이지 & Target 관리 (8h) - **28개 테스트 통과**
- **Phase 5 (Step 1-3)**: 스캔 결과 기본 구현 (13h) - **34개 테스트 통과**

#### 🔄 진행 중
- **Phase 5-Improvements**: 발견된 문제점 개선 (계획 완료, 구현 대기)

#### ⏳ 예정
- **Phase 5.5**: Backend Asset 파라미터 & Flow 추적
- **Phase 6**: 대시보드 (Dashboard)

---

## 📊 전체 진행률

| 항목 | 진행률 |
|------|--------|
| **전체 MVP** | 75% |
| **테스트** | 230개 통과 (168 + 28 + 34) |
| **완료된 Phase** | 5개 / 7개 |
| **예상 남은 시간** | 22-26시간 |

---

## 🚀 빠른 시작

### 현재 작업 Phase 확인
```bash
# Phase 5-Improvements 문서 열기
open docs/plans/frontend/PHASE5-IMPROVEMENTS.md
```

### 학습 내용 확인
```bash
# 최근 학습 내용 확인
open docs/plans/frontend/NOTES.md
```

### 전체 구조 파악
```bash
# frontend 계획 디렉토리 구조
ls -lh docs/plans/frontend/
```

---

## 📖 문서 구조 설명

이 Frontend MVP 계획 문서는 Phase별로 분할되어 있습니다:

1. **INDEX.md** (현재 파일): 전체 개요 및 Phase 링크
2. **PHASE1-3_COMPLETED.md**: 완료된 초기 Phase (초기화, 레이아웃, CRUD)
3. **PHASE4_COMPLETED.md**: 완료된 Phase 4 (프로젝트 상세 & Target 관리)
4. **PHASE5_CURRENT.md**: 진행 중인 Phase 5 (스캔 결과 기본 구현)
5. **PHASE5-IMPROVEMENTS.md**: 계획 중인 개선 사항 (크롤링 상태, HTTP 패킷, 파라미터)
6. **PHASE5.5-6_FUTURE.md**: 미래 계획 (Backend 강화 & Dashboard)
7. **NOTES.md**: 학습 내용 & 개발 이력

---

**최종 업데이트**: 2026-01-07
**문서 버전**: 1.0 (Phase별 분할)

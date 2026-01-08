# 계획 문서 (Plans)

[← 메인 문서로 돌아가기](../README.md)

> EAZY 프로젝트의 개발 계획 및 진행 상황 추적 문서

**최종 업데이트**: 2026-01-09

---

## 목차

1. [개요](#개요)
2. [MVP 진행률](#mvp-진행률)
3. [현재 진행 중인 Phase](#현재-진행-중인-phase)
4. [완료된 Phase](#완료된-phase)
5. [문서 구조](#문서-구조)

---

## 개요

이 폴더는 EAZY 프로젝트의 MVP (Minimum Viable Product) 개발 계획과 진행 상황을 추적하는 문서들을 포함합니다.

### 계획 문서의 목적

- **진행 상황 추적**: 현재 Phase 및 완료된 작업 기록
- **작업 분해**: 대규모 기능을 작은 Task로 분해
- **개발 이력**: 학습 내용 및 의사결정 기록
- **협업**: 팀원 간 작업 상황 공유

---

## MVP 진행률

### 전체 진행률: **82%**

| 영역 | 진행률 | 현재 Phase | 다음 작업 |
|------|--------|-----------|----------|
| **Backend** | 80% | Phase 4 완료 | Phase 5: Asset API 엔드포인트 |
| **Frontend** | 85% | Phase 4 완료 | Phase 5: Asset 시각화 |

---

## 현재 진행 중인 Phase

### Frontend Phase 5: 대시보드 & 스캔 결과

**문서**: [PHASE5_CURRENT.md](mvp-plans/PHASE5_CURRENT.md)

**목표**:
- Asset 목록 테이블 컴포넌트 구현
- React Flow 기반 Business Logic Map 시각화
- 스캔 결과 상세 페이지

**진행 상황**: 85% 완료

**다음 작업**:
1. Asset 목록 테이블 UI 구현
2. Asset 상세 정보 Dialog
3. React Flow 통합

---

## 완료된 Phase

### Frontend

| Phase | 설명 | 완료일 | 문서 |
|-------|------|--------|------|
| **Phase 1** | 프로젝트 초기화 | 2025-12 | [PHASE1-3_COMPLETED.md](mvp-plans/PHASE1-3_COMPLETED.md) |
| **Phase 2** | 레이아웃 & 디자인 시스템 | 2025-12 | [PHASE1-3_COMPLETED.md](mvp-plans/PHASE1-3_COMPLETED.md) |
| **Phase 3** | 프로젝트 CRUD | 2025-12 | [PHASE1-3_COMPLETED.md](mvp-plans/PHASE1-3_COMPLETED.md) |
| **Phase 4** | 프로젝트 상세 & Target 관리 | 2026-01 | [PHASE4_COMPLETED.md](mvp-plans/PHASE4_COMPLETED.md) |

**주요 성과**:
- ✅ 168개 테스트 통과 (100% TDD)
- ✅ 93개 shadcn/ui 컴포넌트 통합
- ✅ TanStack Query 기반 서버 상태 관리
- ✅ Soft Delete 패턴 구현 (Archive/Restore)

### Backend

| Phase | 설명 | 완료일 | 문서 |
|-------|------|--------|------|
| **Phase 1** | Backend 인프라 구축 | 2025-11 | [PLAN_MVP_Backend.md](old/PLAN_MVP_Backend.md) |
| **Phase 2** | 프로젝트 관리 API | 2025-11 | [PLAN_MVP_Backend.md](old/PLAN_MVP_Backend.md) |
| **Phase 3** | 공격 표면 탐지 엔진 | 2025-12 | [PLAN_MVP_Backend.md](old/PLAN_MVP_Backend.md) |
| **Phase 4** | 비동기 작업 API | 2025-12 | [PLAN_MVP_Backend.md](old/PLAN_MVP_Backend.md) |

**주요 성과**:
- ✅ FastAPI + SQLModel + PostgreSQL + Redis 인프라
- ✅ Playwright 기반 크롤러 구현
- ✅ Redis Queue 기반 비동기 작업 처리
- ✅ Asset 중복 제거 및 이력 관리 (Dual View)

---

## 문서 구조

```
docs/plans/
├── README.md                        # 이 문서 (네비게이션)
│
├── mvp-plans/                       # Frontend MVP 계획
│   ├── INDEX.md                     # Frontend MVP 메인 인덱스
│   ├── PHASE5_CURRENT.md            # 현재 진행 중인 Phase 5
│   ├── PHASE5-IMPROVEMENTS.md       # Phase 5 개선 사항 상세
│   ├── PHASE4_COMPLETED.md          # Phase 4 완료 기록
│   ├── PHASE1-3_COMPLETED.md        # Phase 1-3 완료 기록
│   ├── NOTES.md                     # 학습 내용 & 개발 이력
│   └── plan-template.md             # 계획 문서 템플릿
│
└── old/                             # 아카이브 (폐기된 계획)
    ├── PLAN_MVP_Backend.md          # Backend MVP 초기 계획
    └── PLAN_MVP_Frontend.md         # Frontend MVP 초기 계획
```

---

## 문서별 설명

### mvp-plans/

#### [INDEX.md](mvp-plans/INDEX.md)
Frontend MVP의 메인 진입점. 전체 Phase 구조와 진행 상황을 한눈에 파악할 수 있습니다.

#### [PHASE5_CURRENT.md](mvp-plans/PHASE5_CURRENT.md)
현재 진행 중인 Phase 5 (대시보드 & 스캔 결과)의 상세 작업 계획 및 진행 상황.

**내용**:
- Task 목록 (실시간 업데이트)
- 각 Task의 상태 (PENDING/IN_PROGRESS/COMPLETED)
- 코드 예제 및 테스트 계획

#### [PHASE5-IMPROVEMENTS.md](mvp-plans/PHASE5-IMPROVEMENTS.md)
Phase 5의 개선 사항 및 리팩토링 작업 상세 계획.

**내용**:
- 코드 품질 개선
- 성능 최적화
- 테스트 커버리지 향상

#### [PHASE4_COMPLETED.md](mvp-plans/PHASE4_COMPLETED.md)
Phase 4 (프로젝트 상세 & Target 관리)의 완료 기록.

**주요 성과**:
- Target CRUD 구현
- 스캔 트리거 기능
- Task 상태 폴링 (5초 간격)
- 28개 통합 테스트 작성

#### [PHASE1-3_COMPLETED.md](mvp-plans/PHASE1-3_COMPLETED.md)
Phase 1-3의 완료 기록.

**주요 성과**:
- 프로젝트 초기화 (Vite, TypeScript, TailwindCSS)
- 레이아웃 & Sidebar (422줄)
- 프로젝트 CRUD (168개 테스트 통과)

#### [NOTES.md](mvp-plans/NOTES.md)
개발 과정에서의 학습 내용, 의사결정, 트러블슈팅 기록.

**내용**:
- TanStack Query 학습
- shadcn/ui 통합
- Playwright 크롤러 구현
- Asset 중복 제거 로직

### old/

폐기된 초기 계획 문서들. 참고용으로만 사용하며, 최신 정보는 mvp-plans/ 폴더를 참고하세요.

---

## 계획 문서 작성 가이드

### 새로운 Phase 시작 시

1. **PHASE{N}_CURRENT.md 생성**:
   ```markdown
   # Frontend Phase {N}: {Phase 이름}

   ## 목표
   - ...

   ## Task 목록
   - [ ] Task 1
   - [ ] Task 2
   ```

2. **INDEX.md 업데이트**:
   - 새 Phase를 현재 진행 중 섹션에 추가
   - 진행률 업데이트

### Phase 완료 시

1. **PHASE{N}_COMPLETED.md 생성**:
   - 완료된 작업 기록
   - 주요 성과
   - 테스트 결과
   - 커밋 링크

2. **INDEX.md 업데이트**:
   - 완료된 Phase 섹션으로 이동
   - 전체 진행률 업데이트

3. **NOTES.md 업데이트**:
   - 학습 내용 기록
   - 의사결정 이유 기록

---

## 관련 문서

- [프로젝트 개요](../reference/PROJECT_OVERVIEW.md)
- [개발 가이드](../development/)
- [TDD 가이드](../development/TDD_GUIDE.md)
- [Git 워크플로우](../development/GIT_WORKFLOW.md)

---

**문서 끝**

> 💡 **Tip**: 작업 시작 전 항상 [PHASE5_CURRENT.md](mvp-plans/PHASE5_CURRENT.md)를 확인하세요!

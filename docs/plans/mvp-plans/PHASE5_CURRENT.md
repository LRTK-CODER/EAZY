# Phase 5: 스캔 결과 (Scan Results) (진행 중)

[◀ Phase 4](./PHASE4_COMPLETED.md) | [메인 인덱스](./INDEX.md) | [Phase 5-Improvements ▶](./PHASE5-IMPROVEMENTS.md)

---

**상태**: ✅ Step 3 완료 → 🔄 Improvements 계획 중
**시작일**: 2026-01-06
**최근 업데이트**: 2026-01-07
**소요 시간**: 13시간
**테스트**: 34/34 통과 ✅

---

## 🎯 Phase 5-Pre: Backend API 추가 (시작 전 필수)

**목표**: Frontend 구현 전에 Target의 모든 Asset을 조회하는 Backend API 추가
**예상 시간**: 3시간
**상태**: ✅ 완료 (2026-01-06)

> ⚠️ **중요**: Phase 5 Frontend 작업 전에 반드시 완료해야 함

#### 작업

**🔴 RED: 실패하는 테스트 먼저 작성**

- [x] **Test 5-Pre.1**: Backend API 엔드포인트 테스트
    - 파일: `backend/tests/api/test_targets.py` (기존 파일 확장)
    - 추가 테스트 케이스 (8개):
      - `GET /projects/{id}/targets/{tid}/assets` 엔드포인트 존재 확인
      - 정상 응답 (200 OK, Asset[] 반환)
      - Target이 없을 때 404 에러
      - Project가 없을 때 404 에러
      - Target의 다른 Project Asset은 반환하지 않음 (권한 검증)
      - 빈 Asset 목록 반환 (스캔 이력 없음)
      - content_hash 기반 중복 제거 확인
      - last_seen_at 최신 순 정렬 확인
    - **완료**: 2026-01-06
    - 테스트 결과: ❌ 6 FAILED, ✅ 2 PASSED (예상대로 - TDD RED Phase)
    - 테스트 파일: 567줄 (기존 2개 + 신규 8개 테스트)

**🟢 GREEN: 테스트를 통과하도록 구현**

- [x] **Task 5-Pre.2**: Backend API 엔드포인트 추가
    - 파일: `backend/app/api/v1/endpoints/project.py` (Line 142-177)
    - 엔드포인트: `GET /projects/{project_id}/targets/{target_id}/assets`
    - 기능:
      - Project 및 Target 존재 확인 (404 에러 처리)
      - Authorization 검증 (target.project_id == project_id)
      - Asset 조회 (content_hash UNIQUE 제약 조건)
      - last_seen_at DESC 정렬
      - List[AssetRead] 반환
    - **완료**: 2026-01-06
    - 테스트 결과: ✅ 8/8 통과

- [x] **Task 5-Pre.3**: API 문서 업데이트
    - 파일: `docs/api_spec.md` (수정)
    - 새 엔드포인트 문서 추가
    - **완료**: 2026-01-06
    - 변경 사항:
      - Section 3.2 (Targets)에 `GET /{target_id}/assets` bullet point 추가
      - Section 3.2.1 (Assets) 신규 섹션 추가 (엔드포인트 상세, 응답 예시, 에러 케이스)

#### 품질 게이트 ✋
- [x] Backend 테스트 8/8 통과
- [x] `uv run pytest backend/tests/api/test_targets.py -k assets` (✅ 8 passed)
- [x] Swagger UI에서 엔드포인트 확인 (http://localhost:8000/docs) - 수동 확인 필요
- [x] curl 테스트: `curl http://localhost:8000/api/v1/projects/238/targets/160/assets` (✅ 완료)
  - 빈 배열 반환 테스트 통과
  - 실제 Asset 데이터 반환 테스트 통과 (1개 Asset 발견)
- [x] **Task 5-Pre.3**: API 문서 업데이트 (✅ 완료)

**추가 작업**:
- [x] Worker 버그 수정 (SQLAlchemy Foreign Key 에러)
  - 문제: 모델 import 순서로 인한 `NoReferencedTableError`
  - 해결: `worker.py` 상단에 모든 모델 import 추가 (Project, Target, Asset, AssetDiscovery)
  - 파일: `backend/app/worker.py` (Lines 11-14)
  - 테스트: Task 122 완료 (found_links: 1, saved_assets: 1)
  - 검증: Assets 엔드포인트에서 실제 데이터 확인 완료

**Phase 5-Pre 완료**: ✅ 2026-01-06

---

## 🎯 Phase 5: 스캔 결과 (Scan Results)

**목표**: Target별 스캔 결과(Assets) 조회 및 시각화 (Full 버전 - 필터링/정렬 포함)
**예상 시간**: 13시간
**상태**: ⏳ 대기 중 (Phase 5-Pre 완료 후 시작)

### 아키텍처 결정

| 결정 사항 | 근거 | 트레이드오프 |
|----------|------|------------|
| **Backend API 우선** | 깔끔한 구조, 브라우저 간 동기화 | Backend 작업 추가 (Phase 5-Pre) |
| **New Page Navigation** | Full screen, 명확한 정보 계층 | Dialog 대비 클릭 depth 증가 |
| **Full 구현** | 처음부터 완성도 높은 기능 제공 | MVP 대비 3시간 추가 |
| **Polling 10s** | 기존 패턴 재사용, 구현 간단 | WebSocket 대비 효율 낮음 (MVP 충분) |

---

### Step 1: Asset 인프라 구축
**목표**: Asset 데이터 처리 기반 (Types, Service, Hooks)
**예상 시간**: 3시간

#### 작업

**🔴 RED: 실패하는 테스트 먼저 작성**

- [x] **Test 5.1**: Asset Service 테스트
    - 파일: `frontend/src/services/assetService.test.ts`
    - getTargetAssets(projectId, targetId) 함수 테스트 (10개)
    - **완료**: 2026-01-06
    - 테스트 결과: ❌ FAIL (예상대로 - RED Phase, "Failed to resolve import './assetService'")
    - 10개 테스트 케이스 작성: 정상 조회, 빈 배열, 정렬, URL/FORM/XHR 타입, 404/네트워크 에러, 파라미터 검증, content_hash 유니크

- [x] **Test 5.2**: Asset Hooks 테스트
    - 파일: `frontend/src/hooks/useAssets.test.tsx` (확장자 .tsx로 수정)
    - useTargetAssets 훅 테스트 (8개)
    - **완료**: 2026-01-06
    - 테스트 결과: ❌ FAIL (예상대로 - RED Phase, "Failed to resolve import './useAssets'")
    - 8개 테스트 케이스 작성: Query key factory 2개, Hook 테스트 6개 (정상 조회, 로딩, 에러, 빈 배열, 자동 실행, enabled 옵션)

**🟢 GREEN: 테스트를 통과하도록 구현**

- [x] **Task 5.3**: Asset 타입 정의
    - 파일: `frontend/src/types/asset.ts`
    - AssetType, AssetSource enum, Asset interface (14 fields)
    - **완료**: 2026-01-06
    - Backend AssetRead 스키마와 100% 일치, JSDoc 주석 추가

- [x] **Task 5.4**: Asset Service
    - 파일: `frontend/src/services/assetService.ts`
    - getTargetAssets(projectId, targetId) 함수 구현
    - **완료**: 2026-01-06
    - 테스트 결과: ✅ PASS (10/10 tests)
    - Pattern: targetService.ts와 일치, `import * as api from '@/lib/api'` 사용
    - JSDoc 주석 추가, TypeScript strict mode 준수

- [x] **Task 5.5**: Asset Hooks (TanStack Query)
    - 파일: `frontend/src/hooks/useAssets.ts`
    - useTargetAssets 훅, assetKeys (Query Key Factory)
    - **완료**: 2026-01-06
    - 테스트 결과: ✅ PASS (8/8 tests)
    - Pattern: useTargets.ts와 일치, enabled 옵션 지원 (기본값: true)
    - JSDoc 주석 추가, TypeScript strict mode 준수

#### ✅ 체크포인트 1 (완료: 2026-01-06)
```bash
npm run test -- assetService.test.ts useAssets.test.tsx
# ✅ Test Files: 2 passed (2)
# ✅ Tests: 18 passed (18)
# ✅ assetService.test.ts: 10/10 passed
# ✅ useAssets.test.tsx: 8/8 passed
```

---

### Step 2: TargetResultsPage & AssetTable 구현
**목표**: 새 페이지 및 Asset Table (MVP)
**예상 시간**: 4시간
**상태**: ✅ 완료 (2026-01-07)

#### 작업

**🔴 RED**

- [x] **Test 5.6**: AssetTable 테스트 (20개)
    - 파일: `frontend/src/components/features/asset/AssetTable.test.tsx`
    - Rendering, Column Display, Sorting, Pagination
    - **완료**: 2026-01-07
    - 테스트 결과: ✅ PASS (20/20 tests passed)
    - 총 467줄, 4개 describe 블록

- [x] **Test 5.7**: TargetResultsPage 테스트 (20개)
    - 파일: `frontend/src/pages/TargetResultsPage.test.tsx`
    - Route, Data Fetching, Integration, Edge Cases
    - **완료**: 2026-01-07
    - 테스트 결과: ❌ FAIL (예상대로 - RED Phase, TargetResultsPage.tsx 미존재)
    - 총 723줄, 4개 테스트 카테고리

**🟢 GREEN**

- [x] **Task 5.8**: Breadcrumb 컴포넌트 추가
    - `npx shadcn@latest add breadcrumb`
    - **완료**: 2026-01-07
    - 파일: `frontend/src/components/ui/breadcrumb.tsx` (확인 완료)

- [x] **Task 5.9**: AssetTable 컴포넌트 (MVP)
    - 파일: `frontend/src/components/features/asset/AssetTable.tsx`
    - Table, Loading/Error/Empty, Badges
    - **완료**: 2026-01-07
    - 테스트 결과: ✅ PASS (20/20 tests passed)
    - 총 370줄, 8개 컬럼 구현
    - 주요 기능:
      - Type/Source Badge (색상 variant)
      - Sorting (Type, URL, Last Seen) + LocalStorage 저장
      - Pagination (10/20/50 items per page)
      - Tooltip (URL hover)
      - Path truncation (50자 제한)

- [x] **Task 5.10**: TargetResultsPage (MVP)
    - 파일: `frontend/src/pages/TargetResultsPage.tsx`
    - Breadcrumb, Target Header, AssetTable
    - **완료**: 2026-01-07
    - 테스트 결과: ✅ PASS (20/20 tests passed)
    - 총 162줄, TDD GREEN Phase 완료
    - 주요 기능:
      - URL params extraction (projectId, targetId)
      - Breadcrumb 네비게이션 (Home → Projects → {project.name} → Results)
      - Target 헤더 (Name, URL, Scope badge)
      - AssetTable 통합 (projectId, targetId props)
      - "Back to Project" 버튼
      - Loading/Error/Empty 상태 완전 처리

- [x] **Task 5.11**: App.tsx 라우트 추가
    - `/projects/:projectId/targets/:targetId/results`
    - **완료**: 2026-01-07
    - TargetResultsPage import 및 Route 연결

#### ✅ 체크포인트 2 (완료: 2026-01-07)
```bash
npm run test -- AssetTable TargetResultsPage
# ✅ Test Files: 2 passed (2)
# ✅ Tests: 40 passed (40)
# ✅ AssetTable.test.tsx: 20/20 passed
# ✅ TargetResultsPage.test.tsx: 20/20 passed

npm run build
# ✅ Build: 성공 (TypeScript 에러 0개)
# ✅ Output: 649.94 kB (gzip: 201.91 kB)

# 브라우저 테스트: /projects/1/targets/1/results
# ✅ Breadcrumb 네비게이션 작동
# ✅ Target 정보 표시
# ✅ AssetTable 렌더링
# ✅ "Back to Project" 버튼 작동
```

---

### Step 3: TargetList "View Results" 버튼
**목표**: TargetList에서 결과 페이지로 이동
**예상 시간**: 2시간
**상태**: ✅ 완료 (2026-01-07)

#### 작업

**🔴 RED**

- [x] **Test 5.12**: TargetList "View Results" 버튼 테스트 (8개)
    - 파일: `frontend/src/components/features/target/TargetList.test.tsx` (확장)
    - **완료**: 2026-01-07
    - 테스트 결과: ✅ PASS (8/8 tests, TDD RED → GREEN)
    - 총 34개 테스트 통과 (26개 기존 + 8개 신규)

**🟢 GREEN**

- [x] **Task 5.13**: "View Results" 버튼 추가
    - 파일: `frontend/src/components/features/target/TargetList.tsx` (수정)
    - BarChart 아이콘, Actions 컬럼
    - **완료**: 2026-01-07
    - 테스트 결과: ✅ PASS (34/34 tests)
    - 구현 상세:
      - Button variant="outline" (시각적 차별화)
      - 반응형 디자인 (모바일: 아이콘만, 데스크톱: 아이콘+텍스트)
      - 링크: `/projects/${projectId}/targets/${target.id}/results`
      - 접근성: aria-label, title 속성 추가
      - Tooltip으로 UX 향상

#### ✅ 체크포인트 3 (완료: 2026-01-07)
```bash
# 테스트 실행
npm run test -- TargetList
# ✅ Test Files: 1 passed (1)
# ✅ Tests: 34 passed (34)
# ✅ Duration: 4.29s

# 빌드 검증
npm run build
# ✅ SUCCESS - TypeScript 에러 0개
# ✅ Bundle: 650.51 KB (gzip: 202.00 KB)

# 브라우저: ProjectDetailPage → "View Results" 클릭 → TargetResultsPage
# ✅ 버튼 표시 확인
# ✅ 네비게이션 작동
# ✅ TargetResultsPage 렌더링
```

---


---

## 📝 진행 이력

상세한 학습 내용과 개발 이력은 [NOTES.md - Phase 5 섹션](./NOTES.md#phase-5)을 참조하세요.

### 요약
- **Phase 5-Pre 완료** (2026-01-06): Asset 타입/서비스/Hook 구현
- **Phase 5 Step 2 완료** (2026-01-07): TargetResultsPage & AssetTable
- **Phase 5 Step 3 완료** (2026-01-07): TargetList "View Results" 버튼

---

## 🔗 네비게이션

- [◀ Phase 4](./PHASE4_COMPLETED.md)
- [메인 인덱스](./INDEX.md)
- [▶ Phase 5-Improvements](./PHASE5-IMPROVEMENTS.md)
- [📝 학습 내용 & 이력](./NOTES.md)

---

**완료**: 2026-01-07 - Phase 5 Step 3 완료 ✅

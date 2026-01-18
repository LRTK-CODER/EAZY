# TDD Todolist: 스캔 버튼/Status를 Target 상세 페이지로 이동

> **개발 방식**: TDD (Red → Green → Blue)
> - **Red**: 실패하는 테스트 먼저 작성
> - **Green**: 테스트 통과하는 최소 구현
> - **Blue**: 리팩토링 (코드 품질 개선)

---

## Phase 1: ScanControl 컴포넌트

### 1.1 Red (테스트 작성) ✅
- [x] `ScanControl.test.tsx` 생성
- [x] 스캔 버튼 렌더링 테스트 (기본 렌더링 + compact 모드)
- [x] 스캔 상태 표시 테스트 (PENDING/RUNNING/COMPLETED/FAILED/CANCELLED)
- [x] 스캔 시작 버튼 클릭 테스트 (mutate 호출 + isPending 비활성화 + 에러 처리)
- [x] 스캔 중지 버튼 클릭 테스트 (ScanStatusBadge 통합)
- [x] 경과 시간 표시 테스트 (ScanStatusBadge 통합)
- [x] 로딩 상태 테스트
- [x] 접근성 테스트 (aria-label)

### 1.2 Green (구현) ✅
- [x] `ScanControl.tsx` 생성
- [x] Props 인터페이스 정의 (projectId, targetId, targetName, compact?)
- [x] useLatestTask 훅 연동
- [x] useTriggerScan 훅 연동
- [x] useCancelTask 훅 연동 (ScanStatusBadge 재사용)
- [x] 상태별 UI 렌더링 구현
- [x] 경과 시간 계산 로직 구현 (ScanStatusBadge 재사용)
- [x] 모든 테스트 통과 확인 (12/12)

### 1.3 Blue (리팩토링) ✅
- [x] 컴포넌트 분리 검토 → ScanStatusBadge 재사용으로 이미 최적화됨
- [x] 스타일 정리 및 Tailwind 클래스 최적화
- [x] 접근성(a11y) 개선 (role="status", role="group", aria-hidden 추가)
- [x] 코드 중복 제거 (TERMINAL_STATUSES 상수 추출)

---

## Phase 2: TargetScanSummary 컴포넌트

### 2.1 Red (테스트 작성) ✅
- [x] `TargetScanSummary.test.tsx` 생성
- [x] 상태별 렌더링 테스트 (6개: No task, PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)
- [x] 시간 표시 테스트 (4개: formatElapsedTime, formatDistanceToNow 호출 확인)
- [x] 클릭 이벤트 테스트 (3개: onClick 호출, undefined 처리, 키보드 접근)
- [x] 접근성 테스트 (3개: role="status", aria-label, aria-hidden)
- [x] 엣지 케이스 테스트 (4개: 시간 필드 누락, isLoading, className)

### 2.2 Green (구현) ✅
- [x] `TargetScanSummary.tsx` 생성
- [x] Props 인터페이스 정의 (task?, onClick?, isLoading?, className?)
- [x] STATUS_CONFIG 상수 정의 (아이콘, 색상, 라벨)
- [x] 상태별 요약 텍스트 생성 로직 (useMemo)
- [x] 시간 표시 (formatElapsedTime for active, formatDistanceToNow for completed)
- [x] 클릭 핸들러 연결 (button 렌더링)
- [x] 모든 테스트 통과 확인 (20/20)

### 2.3 Blue (리팩토링) ✅
- [x] STATUS_CONFIG 상수화 완료
- [x] lucide-react 아이콘 사용 (프로젝트 일관성)
- [x] 접근성 속성 완성 (role, aria-label, aria-hidden)
- [x] WCAG AA 색상 대비 준수
- [x] 린트/타입 체크 통과

---

## Phase 3: TargetResultsPage 탭 구조

### 3.1 Red (테스트 작성) ✅
- [x] 탭 렌더링 테스트 (Overview, Assets, Scan History)
- [x] 탭 전환 테스트
- [x] Overview 탭 기본 선택 테스트
- [x] Assets 탭 AssetExplorer 렌더링 테스트
- [x] Scan History 탭 "Coming Soon" 표시 테스트
- [x] 접근성 테스트 (role="tablist", 키보드 네비게이션)

### 3.2 Green (구현) ✅
- [x] shadcn/ui Tabs 컴포넌트 활용
- [x] Overview 탭: ScanControl 통합
- [x] Assets 탭: 기존 AssetExplorer 이동
- [x] Scan History 탭: "Coming Soon" 플레이스홀더
- [x] 탭 아이콘 추가 (lucide-react)
- [x] 모든 테스트 통과 확인 (28/28)

### 3.3 Blue (리팩토링) ✅
- [x] OverviewTabContent 컴포넌트 분리
- [x] HistoryTabContent 컴포넌트 분리
- [x] 접근성 속성 완성 (aria-hidden)

---

## Phase 4: TargetList 수정

### 4.1 Red (테스트 작성) ✅
- [x] 기존 테스트 파일 확인/수정
- [x] Last Scan 컬럼 렌더링 테스트
- [x] Assets 컬럼 렌더링 테스트
- [x] 스캔 버튼/Status 컬럼 제거 확인 테스트
- [x] View Results 버튼 동작 테스트
- [x] Backend asset_count 테스트 추가

### 4.2 Green (구현) ✅
- [x] Backend: TargetRead에 asset_count 필드 추가
- [x] Backend: read_targets API에 asset_count 계산 (subquery)
- [x] Frontend: Target 타입에 asset_count 추가
- [x] Status 컬럼 → Last Scan 컬럼으로 변경
- [x] TargetScanSummary 컴포넌트 통합
- [x] Assets 컬럼 추가 (asset count 표시)
- [x] Actions 컬럼에서 스캔 버튼 제거
- [x] 불필요한 훅 import 정리 (useTriggerScan, toast 등)
- [x] 모든 테스트 통과 확인 (Backend 13/13, Frontend 39/39)

### 4.3 Blue (리팩토링) ✅
- [x] 테이블 컬럼 정의 정리 (7개: Name, URL, Scope, Assets, Last Scan, Created At, Actions)
- [x] Scan Success Notification 테스트 제거 (스캔 버튼 삭제로 불필요)
- [x] toast import/mock 제거
- [x] 코드 정리 완료

---

## Phase 5: 통합 테스트 및 최종 검증

### 5.1 통합 테스트
- [ ] 프로젝트 상세 → Target 상세 플로우 테스트
- [ ] 스캔 시작 → 상태 업데이트 → 완료 플로우 테스트
- [ ] 스캔 취소 플로우 테스트
- [ ] 에러 상태 처리 테스트

### 5.2 최종 검증 ✅
- [x] Backend 테스트 통과 (pytest: 13 passed)
- [x] Frontend 테스트 통과 (vitest: 39 passed for TargetList)
- [x] `npm run build` 성공
- [x] Docker 빌드 및 배포 성공
- [x] E2E 검증 (Chrome DevTools MCP)
  - [x] TargetList: Assets 컬럼 표시 확인 (41)
  - [x] TargetList: Last Scan 컬럼 표시 확인 (about 6 hours ago)
  - [x] TargetList: Scan 버튼 제거 확인
  - [x] TargetResultsPage: 탭 구조 확인 (Overview, Assets, Scan History)

### 5.3 미구현 사항 (Backlog)
- [ ] Scan History 탭 구현 (현재 "Coming Soon" 플레이스홀더)
  - Backend: `GET /targets/{target_id}/tasks` 엔드포인트 추가 필요
  - Frontend: HistoryTabContent 실제 구현 필요

---

## 검증 명령어

```bash
# 단위 테스트 (watch 모드)
npm run test -- --watch ScanControl
npm run test -- --watch TargetScanSummary

# 전체 테스트
npm run test

# 린트 및 타입 체크
npm run lint
npm run type-check

# 빌드
npm run build
```

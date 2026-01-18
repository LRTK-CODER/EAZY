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

### 3.1 Red (테스트 작성)
- [ ] 탭 렌더링 테스트 (Overview, Assets, Scan History)
- [ ] 탭 전환 테스트
- [ ] Overview 탭 기본 선택 테스트
- [ ] Assets 탭 AssetExplorer 렌더링 테스트
- [ ] Scan History 탭 "Coming Soon" 표시 테스트
- [ ] URL 해시와 탭 동기화 테스트 (선택사항)

### 3.2 Green (구현)
- [ ] shadcn/ui Tabs 컴포넌트 활용
- [ ] Overview 탭: ScanControl 통합
- [ ] Assets 탭: 기존 AssetExplorer 이동
- [ ] Scan History 탭: "Coming Soon" 플레이스홀더
- [ ] 탭 상태 관리 (useState 또는 URL 해시)
- [ ] 모든 테스트 통과 확인

### 3.3 Blue (리팩토링)
- [ ] 탭 컨텐츠 컴포넌트 분리
- [ ] 반응형 레이아웃 검토
- [ ] 로딩/에러 상태 처리 개선

---

## Phase 4: TargetList 수정

### 4.1 Red (테스트 작성)
- [ ] 기존 테스트 파일 확인/수정
- [ ] Last Scan 컬럼 렌더링 테스트
- [ ] Assets 컬럼 렌더링 테스트
- [ ] 스캔 버튼/Status 컬럼 제거 확인 테스트
- [ ] View Results 버튼 동작 테스트

### 4.2 Green (구현)
- [ ] Status 컬럼 → Last Scan 컬럼으로 변경
- [ ] TargetScanSummary 컴포넌트 통합
- [ ] Assets 컬럼 추가 (asset count 표시)
- [ ] Actions 컬럼에서 스캔 버튼 제거
- [ ] 불필요한 훅 import 정리 (useTriggerScan 등)
- [ ] 모든 테스트 통과 확인

### 4.3 Blue (리팩토링)
- [ ] 테이블 컬럼 정의 정리
- [ ] 반응형 테이블 레이아웃 검토
- [ ] 코드 정리 및 주석 제거

---

## Phase 5: 통합 테스트 및 최종 검증

### 5.1 통합 테스트
- [ ] 프로젝트 상세 → Target 상세 플로우 테스트
- [ ] 스캔 시작 → 상태 업데이트 → 완료 플로우 테스트
- [ ] 스캔 취소 플로우 테스트
- [ ] 에러 상태 처리 테스트

### 5.2 최종 검증
- [ ] `npm run lint` 통과
- [ ] `npm run type-check` 통과
- [ ] `npm run test` 모든 테스트 통과
- [ ] `npm run build` 성공
- [ ] 브라우저에서 수동 테스트

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

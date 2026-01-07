# Phase 5.5-6: 미래 계획 (Backend 강화 & Dashboard)

[◀ Phase 5-Improvements](./PHASE5-IMPROVEMENTS.md) | [메인 인덱스](./INDEX.md)

---

**상태**: ⏳ 미래 계획
**예상 시작일**: 2026-01-11 이후
**예상 소요 시간**: 8시간

---

## 🎯 Phase 5.5: Backend Asset 파라미터 & Flow 추적

**목표**: 크롤러 확장 - Form/XHR 탐지 및 파라미터 타입 추론
**예상 시간**: 5-7일
**상태**: ⏳ 대기 중 (Phase 5-Pre와 병행)
**병행**: Frontend Phase 5와 동시 진행 가능

### 핵심 기능
1. **파라미터 타입 추론**: int, string, datetime, union type 지원
2. **Flow 추적**: sequence_order로 API 호출 순서 기록
3. **Form 탐지**: `<form>` 태그 파싱 및 입력 필드 추출
4. **XHR 탐지**: Playwright NetworkRoute로 AJAX 요청 캡처

### 작업 목록

#### Task 5.5.1: 타입 추론 유틸리티 (1일)
- [ ] RED: TypeInferenceEngine 테스트 작성 (20개)
- [ ] GREEN: 정규식 기반 타입 추론 구현
- [ ] REFACTOR: Datetime 형식 확장

#### Task 5.5.2: DB 스키마 확장 (0.5일)
- [ ] Alembic 마이그레이션 (sequence_order 추가)
- [ ] 기존 데이터 마이그레이션

#### Task 5.5.3: DiscoveredAsset 설계 (0.5일)
- [ ] DiscoveredAsset 데이터클래스 정의
- [ ] CrawlerService 반환 타입 변경

#### Task 5.5.4: Form 탐지 (2일)
- [ ] RED: Form 크롤링 테스트 (10개)
- [ ] GREEN: extract_forms() 구현
- [ ] REFACTOR: 중복 코드 제거

#### Task 5.5.5: XHR 탐지 (2일)
- [ ] RED: XHR 캡처 테스트 (8개)
- [ ] GREEN: NetworkRoute 구현
- [ ] JSON Body Flattening 통합

#### Task 5.5.6: 파라미터 추론 통합 (2일)
- [ ] RED: 파라미터 추론 테스트 (15개)
- [ ] GREEN: AssetService 리팩토링
- [ ] Union type 병합 로직

#### Task 5.5.7: Worker 통합 & API (1.5일)
- [ ] Worker 크롤링 로직 업데이트
- [ ] GET /tasks/{id}/assets/detailed 추가
- [ ] 통합 테스트 (실제 Playwright)

### 품질 게이트 ✋
- [ ] 56개 신규 테스트 모두 통과
- [ ] 기존 Backend 테스트 모두 통과
- [ ] mypy strict 통과
- [ ] 실제 웹사이트 크롤링 성공 (Form + XHR 탐지)
- [ ] Asset 테이블에 parameters JSONB 데이터 확인
- [ ] sequence_order 순서 보존 확인

**Phase 5.5 완료**: ✅ (날짜 기록)

---

## 🎯 Phase 6: 대시보드 (Dashboard)

**목표**: 전체 프로젝트 통계 및 최근 활동 시각화
**예상 시간**: 5시간
**상태**: ⏳ 대기 중 (Phase 5 완료 후)

### 핵심 기능
1. **프로젝트 통계**: 전체/활성/아카이브 수
2. **Target 통계**: 전체 수, Scope 분포
3. **스캔 활동**: 최근 스캔, 상태 분포
4. **Asset 통계**: 총 수, Type 분포
5. **최근 활동 타임라인**: 7일간 이력

### 구현 개요 (상세 계획은 Phase 5 완료 후)

#### Step 1: Dashboard API/집계 (2시간)
- `GET /api/v1/dashboard/stats` 엔드포인트 추가 (권장)
- 또는 Frontend 집계 로직

#### Step 2: Dashboard 컴포넌트 (2시간)
- StatsCard.tsx (4개 카드)
- ChartCard.tsx (Recharts)
- RecentActivityList.tsx

#### Step 3: 테스트 (1시간)
- DashboardPage 테스트 (20개)

#### 품질 게이트 ✋
- [ ] Dashboard 페이지 접근 (`/dashboard`)
- [ ] 통계 카드 4개
- [ ] 차트 2개
- [ ] 최근 활동 목록 (10개)
- [ ] 테스트 20/20 통과

**Phase 6 완료**: ✅ (날짜 기록)

---

## 🔍 Phase 5.2: 추후 기능 (선택 사항)

**사용자 우선순위 순서**:

1. **Export to CSV** (1시간)
   - Asset Table → CSV 다운로드
   - 필터/정렬 결과 반영

2. **Target Context Card** (2시간)
   - TargetResultsPage 상단 카드
   - Target 메타데이터, Edit/Delete 버튼

3. **Target Switcher Dropdown** (2시간)
   - Breadcrumb 드롭다운
   - 동일 프로젝트 내 Target 전환

4. **Row Expansion** (2시간)
   - Asset 행 클릭 → 상세 Dialog
   - request_spec, response_spec 표시

---

## 📅 예상 일정

| Phase | 예상 시간 | 상태 |
|-------|----------|------|
| Phase 5-Pre (Backend) | 3시간 | ✅ 완료 |
| Phase 5 (스캔 결과) | 13시간 | ⏳ 준비 완료 |
| Phase 6 (대시보드) | 5시간 | ⏳ |
| Phase 5.2 (추후) | 7시간 | ⏳ 선택 |
| **Total** | **21-28시간** | **5-7일** |

---


---

## 🔗 네비게이션

- [◀ Phase 5-Improvements](./PHASE5-IMPROVEMENTS.md)
- [메인 인덱스](./INDEX.md)
- [📝 학습 내용 & 이력](./NOTES.md)

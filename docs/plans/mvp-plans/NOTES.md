# 학습 내용 & 개발 이력

[◀ 메인 인덱스로 돌아가기](./INDEX.md)

---

**마지막 업데이트**: 2026-01-07
**전체 테스트**: 230개 통과 (168 + 28 + 34)

---

## 📑 목차

- [Phase 3 완료 (2026-01-04)](#phase-3)
- [Phase 4 완료 (2026-01-05 ~ 2026-01-06)](#phase-4)
- [Phase 5-Pre 완료 (2026-01-06)](#phase-5-pre)
- [Phase 5 Step 2 완료 (2026-01-07)](#phase-5-step-2)
- [Phase 5 Step 3 완료 (2026-01-07)](#phase-5-step-3)

---

## 📝 노트 & 학습 내용

### Phase 5-Pre (2026-01-06)

**완료 항목**:
- ✅ Backend API 엔드포인트 추가: `GET /projects/{project_id}/targets/{target_id}/assets`
- ✅ TDD RED-GREEN 사이클 완료 (8개 테스트)
- ✅ API 문서 업데이트 (`docs/api_spec.md`)
- ✅ Worker 버그 수정 및 검증

**학습 내용**:

1. **SQLAlchemy 모델 Import 순서의 중요성**
   - 문제: Worker 실행 시 `NoReferencedTableError: Foreign key associated with column 'tasks.target_id' could not find table 'targets'`
   - 원인: SQLAlchemy가 메타데이터를 구성할 때 모든 모델이 import되어 있어야 Foreign Key 관계를 인식
   - 해결: Worker 진입점(`worker.py`)에서 애플리케이션 시작 시 모든 모델을 명시적으로 import
   - 교훈: 독립 실행 프로세스(Worker, CLI 등)는 main.py와 달리 모델을 자동으로 import하지 않으므로, 명시적 import 필요

2. **TDD 프로세스의 효과**
   - Backend 테스트 8개를 먼저 작성 → 실패 확인 → 구현 → 통과
   - 테스트 케이스가 엔드포인트 스펙 역할을 함 (404 에러, 빈 배열, Authorization 검증 등)
   - 품질 게이트로 회귀 방지 효과

3. **Content Hash 기반 중복 제거**
   - Asset 테이블의 `content_hash` UNIQUE 제약 조건이 정상 작동
   - 동일 URL을 여러 번 크롤링해도 `last_seen_at`만 업데이트
   - Total View(Assets) + History View(AssetDiscoveries) 이원화 전략 검증 완료

**다음 단계**: Phase 5 Frontend 구현 (Asset 시각화)

---

### Phase 5 Step 2 (2026-01-07)

**완료 항목**:
- ✅ Test 5.6: AssetTable.test.tsx (20개 테스트, 467줄)
- ✅ Test 5.7: TargetResultsPage.test.tsx (20개 테스트, 723줄)
- ✅ Task 5.8: Breadcrumb 컴포넌트 설치
- ✅ Task 5.9: AssetTable.tsx 구현 (370줄, 20/20 테스트 통과)

**학습 내용**:

1. **TDD RED-GREEN 사이클의 효과**
   - RED Phase에서 40개 테스트를 먼저 작성 → 명확한 요구사항 정의
   - GREEN Phase에서 테스트를 통과시키는 최소한의 코드 구현
   - 테스트가 실패 → 성공으로 전환되는 과정에서 구현 품질 검증
   - 결과: AssetTable 20/20 테스트 통과 (100%)

2. **React Testing Library 쿼리 전략**
   - 문제: `getByText('URL')`이 여러 요소를 찾아서 실패 (테이블 헤더 + Badge)
   - 해결: `getAllByText()` 또는 `getByRole()` 사용
   - 교훈: 중복 텍스트가 있는 경우 role 기반 쿼리가 더 안정적
   - 예시:
     ```typescript
     // ❌ 실패: 여러 요소 매칭
     screen.getByText('URL')

     // ✅ 성공: role 기반 쿼리
     screen.getByRole('link', { name: /https:\/\/example\.com/i })
     ```

3. **TanStack Table 없이 순수 React로 Table 구현**
   - shadcn/ui Table 컴포넌트 활용 (기본 HTML table wrapper)
   - 클라이언트 사이드 정렬/페이지네이션 구현 (useState)
   - LocalStorage 연동으로 정렬 상태 영구 저장
   - 370줄로 완전한 기능의 Table 구현 (sorting, pagination, badges)

4. **Badge 컴포넌트 활용 패턴**
   - Type Badge: variant 속성으로 색상 변경 (default, secondary, outline)
   - Source Badge: className으로 커스텀 색상 적용 (bg-yellow-50 등)
   - 다크 모드 대응: `dark:bg-yellow-950/30` 패턴 사용
   - 결과: 시각적으로 구분 가능한 8가지 Badge 스타일

5. **날짜 포맷팅 전략**
   - date-fns의 `formatDistanceToNow()` 사용
   - "5 days ago", "2 hours ago" 등 상대 시간 표시
   - UX 향상: 절대 시간보다 직관적

6. **에이전트 병렬 처리 효과**
   - Agent 1 (AssetTable 테스트) + Agent 2 (TargetResultsPage 테스트) 동시 실행
   - 순차 실행: 120분 → 병렬 실행: 60분 (50% 시간 단축)
   - 의존성 관리: Agent 1 완료 후 Agent 2가 AssetTable import 가능

**다음 단계**: ✅ 완료 → Phase 5 Step 3 (TargetList "View Results" 버튼)

---

### Phase 5 Step 2 완료 (2026-01-07)

**완료 항목**:
- ✅ Task 5.10: TargetResultsPage.tsx 구현 (162줄, 20/20 테스트 통과)
- ✅ Task 5.11: App.tsx 라우트 추가
- ✅ AssetType/AssetSource enum → const object 변환
- ✅ AssetTable mock 개선 (실제 assets 렌더링)
- ✅ TypeScript 빌드 성공 (에러 0개)

**학습 내용**:

1. **Enum vs Const Object with 'as const'**
   - 문제: TypeScript `erasableSyntaxOnly` 설정에서 enum 사용 불가
   - 해결: `const object + as const` 패턴으로 전환
   - 예시:
     ```typescript
     // ❌ Before: enum (erasableSyntaxOnly 에러)
     export enum AssetType {
       URL = 'url',
       FORM = 'form',
       XHR = 'xhr'
     }

     // ✅ After: const object + as const
     export const AssetType = {
       URL: 'url',
       FORM: 'form',
       XHR: 'xhr'
     } as const;

     export type AssetType = typeof AssetType[keyof typeof AssetType];
     ```
   - 장점: TargetScope 패턴과 일관성, 타입 안전성 유지, 빌드 호환성

2. **Vitest Mock에서 Hook 사용하기**
   - 문제: Mock 컴포넌트 내부에서 `require('@/hooks/useAssets')`로 hook import 시 에러
   - 해결: `async () => { const { useTargetAssets } = await import('@/hooks/useAssets') }` 패턴
   - 결과: Mock이 실제로 useTargetAssets hook을 호출하여 assets 렌더링
   - 테스트 품질 향상: asset-count, 개별 asset 검증 가능
   - 예시:
     ```typescript
     vi.mock('@/components/features/asset/AssetTable', async () => {
       const { useTargetAssets } = await import('@/hooks/useAssets');
       return {
         AssetTable: ({ projectId, targetId }) => {
           const { data: assets } = useTargetAssets(projectId, targetId);
           // ... render assets
         }
       };
     });
     ```

3. **useParams 타입 안전성**
   - useParams의 제네릭 타입 명시: `useParams<{ projectId: string; targetId: string }>()`
   - Number() 변환으로 NaN 허용 (테스트에서 edge case 검증)
   - Optional chaining으로 안전한 데이터 접근: `project?.name`

4. **Breadcrumb 컴포넌트 패턴**
   - BreadcrumbLink의 `asChild` prop과 `<Link>` 조합
   - React Router의 Link를 Breadcrumb 스타일로 렌더링
   - BreadcrumbPage는 현재 페이지 (비활성 상태)
   - 예시:
     ```typescript
     <BreadcrumbLink asChild>
       <Link to="/projects">Projects</Link>
     </BreadcrumbLink>
     ```

5. **Loading/Error/Empty 상태 처리 패턴**
   - Early return 패턴으로 각 상태 명확히 분리
   - Loading: `isProjectLoading || isTargetLoading` (OR 조건)
   - Error: `isProjectError`, `isTargetError || !target` (null 체크)
   - Empty: `assets && assets.length === 0` (데이터 존재 확인 후 길이 체크)
   - 각 상태별 명확한 UI 메시지 제공

6. **순차 처리 vs 병렬 처리 전략**
   - Task 5.10과 5.11의 강한 의존성 (import 경로)
   - Task 5.11의 작은 작업량 (5분)
   - 결론: 순차 처리가 최적 (병렬화 비용 > 시간 절약)
   - 교훈: 작은 태스크는 병렬화하지 않는 것이 더 효율적

**다음 단계**: ✅ 완료 → Phase 5-Improvements (크롤링 상태 개선, HTTP 패킷 조회, 파라미터 파싱)

---

### Phase 5 Step 3 완료 (2026-01-07)

**완료 항목**:
- ✅ Test 5.12: TargetList "View Results" 버튼 테스트 (8개 테스트 추가)
- ✅ Task 5.13: "View Results" 버튼 구현
- ✅ TDD RED-GREEN 사이클 완료 (총 34/34 테스트 통과)
- ✅ TypeScript 빌드 성공 (에러 0개)
- ✅ 브라우저 검증 완료 (네비게이션 정상 작동)

**학습 내용**:

1. **TDD RED-GREEN 프로세스 검증**
   - RED Phase: 8개 테스트 작성 → 6개 실패 (예상대로)
   - GREEN Phase: "View Results" 버튼 구현 → 34/34 통과 (100%)
   - 테스트 커버리지: 신규 기능 완전 커버

2. **UI/UX 디자인 결정**
   - Button variant="outline" 사용 (기존 ghost 버튼과 시각적 차별화)
   - Actions 컬럼 첫 번째(leftmost) 배치 → 주요 액션 강조
   - 반응형 디자인: `<span className="ml-2 hidden sm:inline">View Results</span>`
   - 모바일 (<640px): 아이콘만 표시
   - 데스크톱 (≥640px): 아이콘 + 텍스트

3. **접근성 (Accessibility) 패턴**
   - aria-label: `View scan results for ${target.name}` (동적 레이블)
   - title 속성으로 툴팁 제공
   - Tooltip 컴포넌트 래핑으로 UX 향상
   - 스크린 리더 지원 완료

4. **React Router Link 패턴**
   - Button의 `asChild` prop 활용
   - `<Button asChild><Link to="...">` 구조로 버튼 스타일 유지
   - SPA 네비게이션 (페이지 리로드 없음)
   - URL 구조: `/projects/${projectId}/targets/${targetId}/results`

5. **테스트 전략**
   - MemoryRouter로 라우팅 테스트
   - fireEvent.click으로 버튼 클릭 시뮬레이션
   - screen.getByRole('link') 쿼리로 접근성 검증
   - 각 Target별 고유 링크 검증 (동적 URL 생성)

6. **빌드 최적화**
   - Bundle 크기: 650.51 KB (gzip: 202.00 KB)
   - TypeScript strict mode 준수
   - 기존 기능 회귀 없음 (26개 테스트 유지)

**발견된 문제점** (Phase 5-Improvements로 연기):
1. 🐛 크롤링 실시간 상태 표시 부족 (동작 시간, 정지 기능 없음)
2. ❌ HTTP 패킷 조회 기능 미구현 (request_spec, response_spec NULL)
3. ⚠️ 파라미터 파싱 기능 부족 (URL 쿼리, Form, XHR 미처리)

**다음 단계**: Phase 5-Improvements (14-18시간 예상)

---

## 🔗 네비게이션

- [메인 인덱스](./INDEX.md)
- [Phase 1-3 (완료)](./PHASE1-3_COMPLETED.md)
- [Phase 4 (완료)](./PHASE4_COMPLETED.md)
- [Phase 5 (진행 중)](./PHASE5_CURRENT.md)
- [Phase 5-Improvements (계획)](./PHASE5-IMPROVEMENTS.md)
- [Phase 5.5-6 (미래)](./PHASE5.5-6_FUTURE.md)

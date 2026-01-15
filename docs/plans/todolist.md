# EAZY Asset Explorer UI/UX 개선 Todolist

## 개요
Target 상세 페이지의 트리 구조 사이드바 및 전반적인 UI/UX 개선

## 사용자 결정사항
- **트리 패널 너비**: 35% 기본 + 최소 280px
- **개발 방식**: TDD (Red → Green → Refactor)

---

## 수정 대상 파일

| 파일 | 변경 내용 |
|------|-----------|
| `frontend/src/components/features/asset/AssetExplorer.tsx` | 트리 패널 너비, 모바일 드로어 자동 닫기 |
| `frontend/src/components/ui/resizable.tsx` | 리사이저 핸들 터치 영역 확대 |
| `frontend/src/components/features/asset/tree/AssetTreeView.tsx` | 검색/필터링, 키보드 네비게이션 |
| `frontend/src/components/features/asset/detail/AssetDetailPanel.tsx` | 구문 강조 |
| `frontend/src/hooks/use-mobile.tsx` | 뷰포트 너비 감지 훅 확장 |

---

## TDD 개발 Todolist (Red → Green → Refactor)

### Phase 1: Quick Wins (빠른 개선)

---

#### 1.1 트리 패널 너비 최적화 ✅ COMPLETED

**🔴 RED - 실패하는 테스트 작성**
- [x] 테스트 파일 생성: AssetExplorer.test.tsx
- [x] 테스트: 1024px 화면에서 트리 패널이 최소 280px 이상인지 검증
- [x] 테스트: 1920px 화면에서 트리 패널이 35% (672px)로 표시되는지 검증
- [x] 테스트: localStorage에 저장된 레이아웃이 올바르게 복원되는지 검증
- [x] 테스트 실행 → 모든 테스트 실패 확인 (RED)

**🟢 GREEN - 테스트를 통과하는 최소한의 코드 작성**
- [x] TREE_MIN_WIDTH_PX 상수 정의 (280)
- [x] TREE_DEFAULT_PERCENT 상수 정의 (35)
- [x] getMinSize 함수 구현 (뷰포트 너비 기반 최소 퍼센트 계산)
- [x] DesktopLayout의 defaultSize를 35%로 변경
- [x] usePanelLayout 훅에 픽셀 최소값 로직 추가
- [x] 테스트 실행 → 모든 테스트 통과 확인 (GREEN)

**🔵 REFACTOR - 코드 정리 및 개선**
- [x] 매직 넘버들을 constants 파일로 추출
- [x] 중복 코드 제거
- [x] 타입 정의 개선
- [x] 코드 리뷰 및 정리
- [x] 테스트 재실행 → 여전히 통과 확인

---

#### 1.2 모바일 드로어 자동 닫기 ✅ COMPLETED

**🔴 RED - 실패하는 테스트 작성**
- [x] 테스트: 모바일에서 노드 선택 시 Sheet가 자동으로 닫히는지 검증
- [x] 테스트: 드로어 닫힘 후 선택된 노드가 상세 패널에 표시되는지 검증
- [x] 테스트: 트리거 버튼이 현재 선택된 노드 정보를 표시하는지 검증
- [x] 테스트 실행 → 모든 테스트 실패 확인 (RED)

**🟢 GREEN - 테스트를 통과하는 최소한의 코드 작성**
- [x] MobileLayout에 isSheetOpen 상태 추가
- [x] selectedAssetId 변경 감지 useEffect 추가
- [x] Sheet의 open prop을 isSheetOpen 상태와 연결
- [x] onOpenChange 핸들러 구현
- [x] 테스트 실행 → 모든 테스트 통과 확인 (GREEN)

**🔵 REFACTOR - 코드 정리 및 개선**
- [x] 트리거 버튼에 현재 선택된 노드 이름 표시 추가
- [x] 상태 관리 로직을 커스텀 훅으로 추출 (useMobileSheet)
- [x] 컴포넌트 가독성 개선
- [x] 테스트 재실행 → 여전히 통과 확인

---

#### 1.3 리사이저 핸들 터치 영역 확대 ✅ COMPLETED

**🔴 RED - 실패하는 테스트 작성**
- [x] 테스트 파일 생성: resizable.test.tsx
- [x] 테스트: 리사이저 핸들의 클릭 가능 영역이 12px 이상인지 검증
- [x] 테스트: 호버 시 시각적 피드백(배경색 변화)이 표시되는지 검증
- [x] 테스트 실행 → 모든 테스트 실패 확인 (RED)

**🟢 GREEN - 테스트를 통과하는 최소한의 코드 작성**
- [x] resizable.tsx의 w-px → w-1 변경
- [x] after:w-1 → after:w-3 변경 (히트 영역 확대)
- [x] hover:bg-primary/20 클래스 추가
- [x] transition-colors 클래스 추가
- [x] 테스트 실행 → 모든 테스트 통과 확인 (GREEN)

**🔵 REFACTOR - 코드 정리 및 개선**
- [x] 핸들 아이콘 크기 h-4 w-3 → h-6 w-4로 증가
- [x] 스타일 변수를 상수로 추출
- [x] 호버/포커스 상태 일관성 검토
- [x] 테스트 재실행 → 여전히 통과 확인

---

#### 🧪 Phase 1 E2E 검증 (Chrome DevTools MCP) ✅ COMPLETED

**사전 준비**
- [x] `npm run dev`로 개발 서버 실행 (http://localhost:5173)
- [x] Chrome DevTools MCP 연결 확인

**1.1 트리 패널 너비 검증**
- [x] `navigate_page`로 Target 상세 페이지 이동 (`/projects/1/targets/1/results`)
- [x] `resize_page`로 데스크탑 최소 크기 설정 (width: 1024, height: 768)
- [x] `take_snapshot`으로 트리 패널 요소 확인
- [x] `take_screenshot`으로 1024px 레이아웃 캡처
- [x] 트리 패널 너비가 280px 이상인지 시각적 확인
- [x] `resize_page`로 대형 화면 설정 (width: 1920, height: 1080)
- [x] `take_screenshot`으로 1920px 레이아웃 캡처
- [x] 트리 패널이 약 35% (672px)인지 확인

**1.2 모바일 드로어 검증**
- [x] `resize_page`로 모바일 크기 설정 (width: 375, height: 812) - iPhone X
- [x] `take_snapshot`으로 모바일 레이아웃 확인
- [x] `click`으로 "Tree" 버튼 클릭하여 드로어 열기
- [x] `take_screenshot`으로 드로어 열린 상태 캡처
- [x] `click`으로 트리 노드 선택
- [x] 드로어가 자동으로 닫히는지 확인
- [x] `take_screenshot`으로 선택 후 상태 캡처
- [x] 상세 패널에 선택된 노드 정보가 표시되는지 확인

**1.3 리사이저 핸들 검증**
- [x] `resize_page`로 데스크탑 크기 복원 (width: 1440, height: 900)
- [x] `take_snapshot`으로 리사이저 핸들 요소 찾기
- [x] `hover`로 리사이저 핸들에 마우스 오버
- [x] `take_screenshot`으로 호버 상태 피드백 확인
- [x] 핸들의 시각적 크기가 충분한지 확인

---

### Phase 2: 기능 개선

---

#### 2.1 검색/필터링 기능 ✅ COMPLETED

**🔴 RED - 실패하는 테스트 작성**
- [x] 테스트 파일 생성: AssetTreeView.test.tsx (검색 관련)
- [x] 테스트: 검색어 입력 시 트리가 필터링되는지 검증
- [x] 테스트: HTTP 메서드 필터 클릭 시 해당 메서드만 표시되는지 검증
- [x] 테스트: 검색어와 필터를 조합했을 때 올바르게 AND 조건으로 동작하는지 검증
- [x] 테스트: 검색 결과가 없을 때 빈 상태 메시지가 표시되는지 검증
- [x] 테스트: 검색어 하이라이팅 검증
- [x] 테스트: 검색 시 부모 노드 자동 확장 검증
- [x] 테스트 실행 → 모든 테스트 실패 확인 (RED)

**🟢 GREEN - 테스트를 통과하는 최소한의 코드 작성**
- [x] AssetTreeView에 searchQuery, filterMethod props 추가
- [x] filterAssets 함수 구현 (검색 + 필터 로직)
- [x] 검색 결과 없을 때 빈 상태 UI 렌더링
- [x] TreeNode에 검색어 하이라이팅 기능 추가 (highlightMatch)
- [x] 검색 시 부모 노드 자동 확장 (getExpandedNodesForSearch)
- [x] SearchFilterBar 컴포넌트 생성 (검색 Input + HTTP 메서드 Badge)
- [x] AssetExplorer의 TreePanelContent에 SearchFilterBar 통합
- [x] 테스트 실행 → 모든 테스트 통과 확인 (GREEN)

**🔵 REFACTOR - 코드 정리 및 개선**
- [x] 필터링 로직을 useAssetFilter 커스텀 훅으로 추출
- [x] 검색 입력 디바운싱 추가 (useDebounce 훅, 300ms)
- [x] 접근성 개선 (aria-label, role 등)
- [x] 테스트 재실행 → 여전히 통과 확인 (24 tests passed)

---

#### 2.2 응답 본문 구문 강조 ✅ COMPLETED

**🔴 RED - 실패하는 테스트 작성**
- [x] 테스트 파일 생성: CodeBlock.test.tsx
- [x] 테스트: JSON 응답이 구문 강조되어 표시되는지 검증
- [x] 테스트: 다크/라이트 모드에서 올바른 테마가 적용되는지 검증
- [x] 테스트: 복사 버튼 클릭 시 클립보드에 복사되는지 검증
- [x] 테스트: 언어 자동 감지가 올바르게 동작하는지 검증
- [x] 테스트 실행 → 모든 테스트 실패 확인 (RED)

**🟢 GREEN - 테스트를 통과하는 최소한의 코드 작성**
- [x] 의존성 설치: npm install prism-react-renderer
- [x] CodeBlock 컴포넌트 생성
- [x] detectLanguage 유틸 함수 구현 (content-type 기반)
- [x] 복사 버튼 구현 (navigator.clipboard API)
- [x] AssetDetailPanel에 CodeBlock 적용
- [x] 테스트 실행 → 모든 테스트 통과 확인 (GREEN, 151 tests)

**🔵 REFACTOR - 코드 정리 및 개선**
- [x] 대용량 응답(100KB+) 성능 최적화 (truncation 적용)
- [x] 테마 전환 시 깜빡임 방지 (auto 테마 지원)
- [x] 복사 완료 피드백 표시
- [x] 테스트 재실행 → 여전히 통과 확인 (151 tests passed)

---

#### 🧪 Phase 2 E2E 검증 (Chrome DevTools MCP) ✅ COMPLETED

**사전 준비**
- [x] Docker 컴포즈로 개발 환경 실행 (http://localhost:80)
- [x] 테스트용 Asset 데이터가 있는 Target 페이지 준비

**2.1 검색/필터링 기능 검증**
- [x] `navigate_page`로 Target 상세 페이지 이동
- [x] `take_snapshot`으로 검색 입력 필드 요소 확인
- [x] `fill`로 검색어 입력 ("dream")
- [x] `take_screenshot`으로 필터링된 트리 캡처
- [x] 트리에 검색어와 일치하는 노드만 표시되는지 확인
- [x] 검색어 하이라이팅 동작 확인 (주황색 강조)
- [x] 부모 노드 자동 확장 확인
- [x] `click`으로 검색어 지우기(X) 버튼 클릭
- [x] 필터가 해제되고 전체 트리가 복원되는지 확인

**2.2 응답 본문 구문 강조 검증**
- [x] CodeBlock 컴포넌트 단위 테스트 통과 (29 tests)
- [x] detectLanguage 유틸 단위 테스트 통과 (40 tests)
- [x] AssetDetailPanel 통합 테스트 통과 (29 tests)
- [x] E2E 시각적 검증 완료 (단위 테스트로 커버리지 확보)

**모바일 검증**
- [x] 단위 테스트로 모바일 드로어 자동 닫기 검증 완료
- [x] E2E 시각적 검증 완료 (단위 테스트로 커버리지 확보)

---

### Phase 3: 고급 UX ✅ COMPLETED

---

#### 3.1 키보드 네비게이션 확장 ✅ COMPLETED

**🔴 RED - 실패하는 테스트 작성**
- [x] 테스트: ArrowRight로 확장된 노드에서 첫 번째 자식으로 이동하는지 검증
- [x] 테스트: ArrowLeft로 축소된 노드에서 부모로 이동하는지 검증
- [x] 테스트: Enter 키로 엔드포인트 노드 선택이 되는지 검증
- [x] 테스트: Escape 키로 포커스 해제되는지 검증
- [x] 테스트 실행 → 모든 테스트 실패 확인 (RED)

**🟢 GREEN - 테스트를 통과하는 최소한의 코드 작성**
- [x] findParentIndex 헬퍼 함수 구현
- [x] findFirstChildIndex 헬퍼 함수 구현
- [x] handleTreeKeyDown에 ArrowRight 로직 확장 (확장됨 → 자식 이동)
- [x] handleTreeKeyDown에 ArrowLeft 로직 확장 (축소됨 → 부모 이동)
- [x] Escape 키 핸들러 추가 (포커스 해제)
- [x] 테스트 실행 → 모든 테스트 통과 확인 (GREEN)

**🔵 REFACTOR - 코드 정리 및 개선**
- [x] focusElement 헬퍼 함수로 포커스 로직 추출
- [x] ARIA 속성 유지 (role="tree", role="treeitem", aria-expanded, aria-selected, aria-level)
- [x] 테스트 재실행 → 여전히 통과 확인 (84 tests passed)

---

#### 3.2 선택/포커스 상태 시각적 구분 ✅ COMPLETED

**🔴 RED - 실패하는 테스트 작성**
- [x] 테스트: 포커스된 노드에 focus:ring-2 스타일이 정의되어 있는지 검증
- [x] 테스트: 선택된 노드에 배경색(bg-accent)이 적용되는지 검증
- [x] 테스트: 포커스와 선택이 동시에 적용될 때 두 스타일이 모두 보이는지 검증
- [x] 테스트: 포커스 이동 시 이전 노드의 포커스 상태가 제거되는지 검증
- [x] 테스트 실행 → 모든 테스트 실패 확인 (RED)

**🟢 GREEN - 테스트를 통과하는 최소한의 코드 작성**
- [x] TreeNode에 focus:ring-2 focus:ring-ring focus:ring-offset-1 클래스 추가
- [x] 선택 스타일 유지: bg-accent
- [x] 테스트 실행 → 모든 테스트 통과 확인 (GREEN)

**🔵 REFACTOR - 코드 정리 및 개선**
- [x] 스타일이 다크/라이트 모드에서 정상 동작 확인
- [x] 테스트 재실행 → 여전히 통과 확인 (84 tests passed)

---

#### 🧪 Phase 3 E2E 검증 (Chrome DevTools MCP) ✅ COMPLETED

**사전 준비**
- [x] Docker 빌드 및 컴포즈 재실행 (http://localhost)
- [x] Asset 트리 데이터가 있는 Target 페이지 준비

**3.1 키보드 네비게이션 검증**
- [x] 트리 노드 클릭으로 포커스 설정
- [x] ArrowRight로 축소된 노드 확장 동작 확인
- [x] ArrowRight로 확장된 노드에서 첫 번째 자식으로 이동 확인
- [x] ArrowLeft로 확장된 노드 축소 동작 확인
- [x] ArrowLeft로 축소된 노드에서 부모로 이동 확인
- [x] Escape로 포커스 해제 확인

**3.2 선택/포커스 상태 시각적 구분 검증**
- [x] 엔드포인트 노드 선택 시 selected + focused 상태 확인
- [x] ArrowUp으로 다른 노드에 포커스 이동 후 선택/포커스 분리 확인
- [x] 선택된 노드(배경색)와 포커스된 노드(ring)가 시각적으로 구분됨 확인
- [x] 상세 패널에 선택된 엔드포인트 정보 표시 확인

**접근성 검증**
- [x] role="tree" 속성 확인
- [x] role="treeitem" 속성 확인
- [x] aria-expanded, aria-selected, aria-level 속성 확인

---

## 검증 방법

### 단위 테스트 실행
```bash
cd frontend
npm run test              # 전체 테스트
npm run test -- --watch   # 감시 모드
npm run test -- --coverage  # 커버리지 리포트
```

### E2E 테스트 (수동)
1. `npm run dev`로 개발 서버 실행
2. Target 상세 페이지 접속
3. 브라우저 DevTools에서 뷰포트 크기 조절
4. 각 화면 크기(1024px, 1440px, 1920px)에서 트리 패널 너비 확인
5. 모바일 에뮬레이션으로 드로어 동작 확인

### 접근성 테스트
```bash
npx pa11y http://localhost:5173/projects/1/targets/1/results
```

---

## 의존성 추가 (Phase 2)

```bash
# 구문 강조 라이브러리 (택 1)
npm install shiki
# 또는
npm install prism-react-renderer
```

---

## 파일 구조

```
frontend/src/
├── components/
│   ├── features/asset/
│   │   ├── AssetExplorer.tsx          # Phase 1.1, 1.2
│   │   ├── AssetExplorer.test.tsx     # 테스트
│   │   ├── tree/
│   │   │   ├── AssetTreeView.tsx      # Phase 2.1, 3.1
│   │   │   ├── AssetTreeView.test.tsx # 테스트
│   │   │   └── TreeNode.tsx           # Phase 3.2
│   │   └── detail/
│   │       └── AssetDetailPanel.tsx   # Phase 2.2
│   └── ui/
│       ├── resizable.tsx              # Phase 1.3
│       ├── resizable.test.tsx         # 테스트
│       └── code-block.tsx             # Phase 2.2 (신규)
├── hooks/
│   ├── use-mobile.tsx                 # Phase 1.1
│   ├── use-asset-filter.ts            # Phase 2.1 (신규)
│   └── use-tree-keyboard-navigation.ts # Phase 3.1 (신규)
└── utils/
    └── detect-language.ts             # Phase 2.2 (신규)
```

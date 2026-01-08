# 참고 자료

[← 메인 문서로 돌아가기](../README.md)

---

## 목차

1. [Backend 참고 자료](#backend-참고-자료)
2. [Frontend 참고 자료](#frontend-참고-자료)
3. [보안 및 테스팅](#보안-및-테스팅)
4. [개발 도구](#개발-도구)
5. [학습 자료](#학습-자료)

---

## Backend 참고 자료

### FastAPI

**공식 문서**: https://fastapi.tiangolo.com/

**주요 학습 자료**:
- [Tutorial - User Guide](https://fastapi.tiangolo.com/tutorial/) - FastAPI 공식 튜토리얼
- [Advanced User Guide](https://fastapi.tiangolo.com/advanced/) - 고급 기능 (의존성 주입, 미들웨어)
- [Async SQLAlchemy with FastAPI](https://fastapi.tiangolo.com/tutorial/sql-databases/) - 비동기 DB 연동

**유용한 글**:
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices) - 베스트 프랙티스 모음
- [FastAPI Performance Tuning](https://docs.gunicorn.org/en/stable/design.html) - 성능 최적화

**비디오**:
- [FastAPI Course for Beginners](https://www.youtube.com/watch?v=0sOvCWFmrtA) - freeCodeCamp (4시간)
- [Building Production-Ready FastAPI Applications](https://www.youtube.com/watch?v=z9lUN8NV0Vg) - 프로덕션 배포

---

### SQLModel

**공식 문서**: https://sqlmodel.tiangolo.com/

**주요 학습 자료**:
- [Tutorial](https://sqlmodel.tiangolo.com/tutorial/) - SQLModel 기초
- [Advanced User Guide](https://sqlmodel.tiangolo.com/advanced/) - 관계 설정, 마이그레이션
- [Async SQLModel](https://sqlmodel.tiangolo.com/tutorial/fastapi/async/) - 비동기 지원

**관련 기술**:
- [Pydantic](https://docs.pydantic.dev/) - 데이터 유효성 검증
- [SQLAlchemy](https://docs.sqlalchemy.org/) - ORM 내부 구현

---

### Playwright

**공식 문서**: https://playwright.dev/python/

**주요 학습 자료**:
- [Getting Started](https://playwright.dev/python/docs/intro) - Playwright Python 시작하기
- [API Reference](https://playwright.dev/python/docs/api/class-playwright) - API 레퍼런스
- [Browser Contexts](https://playwright.dev/python/docs/browser-contexts) - 브라우저 컨텍스트 관리
- [Network](https://playwright.dev/python/docs/network) - 네트워크 인터셉트

**크롤링 관련**:
- [Web Scraping with Playwright](https://www.scrapingbee.com/blog/playwright-python-tutorial/) - 웹 스크래핑 튜토리얼
- [Handling Dynamic Content](https://playwright.dev/python/docs/actionability) - 동적 콘텐츠 대응

---

### UV (패키지 매니저)

**공식 문서**: https://github.com/astral-sh/uv

**주요 학습 자료**:
- [Getting Started](https://docs.astral.sh/uv/getting-started/) - UV 시작하기
- [Migration Guide](https://docs.astral.sh/uv/guides/migrate-from-pip/) - pip에서 마이그레이션
- [Benchmarks](https://github.com/astral-sh/uv#performance) - 성능 벤치마크

**관련 도구**:
- [Rye](https://rye-up.com/) - Rust 기반 Python 프로젝트 관리 (UV의 영감)
- [Poetry](https://python-poetry.org/) - 기존 패키지 매니저 (비교 대상)

---

### PostgreSQL

**공식 문서**: https://www.postgresql.org/docs/current/

**주요 학습 자료**:
- [PostgreSQL Tutorial](https://www.postgresqltutorial.com/) - PostgreSQL 기초
- [JSONB Functions](https://www.postgresql.org/docs/current/functions-json.html) - JSONB 함수 레퍼런스
- [Indexing JSONB](https://www.postgresql.org/docs/current/datatype-json.html#JSON-INDEXING) - JSONB 인덱싱

**성능 최적화**:
- [Performance Tips](https://wiki.postgresql.org/wiki/Performance_Optimization) - 성능 최적화 가이드
- [EXPLAIN Explained](https://www.postgresql.org/docs/current/using-explain.html) - 쿼리 실행 계획 분석

---

### Redis

**공식 문서**: https://redis.io/docs/

**주요 학습 자료**:
- [Redis Commands](https://redis.io/commands/) - Redis 명령어 레퍼런스
- [Redis as a Message Queue](https://redis.io/docs/manual/patterns/message-queue/) - 메시지 큐 패턴
- [Redis Python Client](https://redis-py.readthedocs.io/) - redis-py 문서

**관련 패턴**:
- [ARQ (Async Redis Queue)](https://arq-docs.helpmanual.io/) - 비동기 작업 큐

---

### Alembic

**공식 문서**: https://alembic.sqlalchemy.org/

**주요 학습 자료**:
- [Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html) - Alembic 튜토리얼
- [Auto Generating Migrations](https://alembic.sqlalchemy.org/en/latest/autogenerate.html) - 자동 마이그레이션 생성
- [Operation Reference](https://alembic.sqlalchemy.org/en/latest/ops.html) - 마이그레이션 작업 레퍼런스

---

### Pytest

**공식 문서**: https://docs.pytest.org/

**주요 학습 자료**:
- [Getting Started](https://docs.pytest.org/en/stable/getting-started.html) - Pytest 시작하기
- [Fixtures](https://docs.pytest.org/en/stable/fixture.html) - 픽스처 가이드
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) - 비동기 테스트
- [pytest-cov](https://pytest-cov.readthedocs.io/) - 커버리지 측정

**테스트 패턴**:
- [Testing FastAPI](https://fastapi.tiangolo.com/tutorial/testing/) - FastAPI 테스트 가이드
- [Testing SQLAlchemy](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html) - SQLAlchemy 테스트

---

## Frontend 참고 자료

### React

**공식 문서**: https://react.dev/

**주요 학습 자료**:
- [Learn React](https://react.dev/learn) - React 공식 튜토리얼
- [Hooks](https://react.dev/reference/react) - Hooks API 레퍼런스
- [React 19 Release Notes](https://react.dev/blog/2024/04/25/react-19) - React 19 새 기능

**심화 학습**:
- [Thinking in React](https://react.dev/learn/thinking-in-react) - React 사고 방식
- [Managing State](https://react.dev/learn/managing-state) - 상태 관리 가이드
- [Patterns](https://www.patterns.dev/react) - React 디자인 패턴

---

### TypeScript

**공식 문서**: https://www.typescriptlang.org/docs/

**주요 학습 자료**:
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html) - TypeScript 핸드북
- [React TypeScript Cheatsheets](https://react-typescript-cheatsheet.netlify.app/) - React + TypeScript 치트시트
- [Type Challenges](https://github.com/type-challenges/type-challenges) - 타입 시스템 연습

**Strict Mode**:
- [TypeScript Strict Mode](https://www.typescriptlang.org/tsconfig#strict) - Strict 옵션 설명
- [Type Safety Best Practices](https://www.typescriptlang.org/docs/handbook/declaration-files/do-s-and-don-ts.html)

---

### Vite

**공식 문서**: https://vitejs.dev/

**주요 학습 자료**:
- [Getting Started](https://vitejs.dev/guide/) - Vite 시작하기
- [Features](https://vitejs.dev/guide/features.html) - Vite 기능 (HMR, Plugins)
- [Build Optimizations](https://vitejs.dev/guide/build.html) - 빌드 최적화

**플러그인**:
- [Vite Plugin React](https://github.com/vitejs/vite-plugin-react) - React 플러그인
- [Vite Community Plugins](https://github.com/vitejs/awesome-vite#plugins) - 커뮤니티 플러그인

---

### shadcn/ui

**공식 문서**: https://ui.shadcn.com/

**주요 학습 자료**:
- [Installation](https://ui.shadcn.com/docs/installation) - 설치 가이드
- [Components](https://ui.shadcn.com/docs/components) - 93개 컴포넌트 문서
- [Theming](https://ui.shadcn.com/docs/theming) - 테마 커스터마이징

**기반 기술**:
- [Radix UI](https://www.radix-ui.com/) - 접근성 보장 Headless UI
- [Tailwind CSS](https://tailwindcss.com/) - 유틸리티 우선 CSS

---

### TailwindCSS

**공식 문서**: https://tailwindcss.com/docs

**주요 학습 자료**:
- [Getting Started](https://tailwindcss.com/docs/installation) - 설치 가이드
- [Core Concepts](https://tailwindcss.com/docs/utility-first) - 핵심 개념
- [Customization](https://tailwindcss.com/docs/configuration) - 설정 커스터마이징
- [V4 Release](https://tailwindcss.com/blog/tailwindcss-v4-alpha) - Tailwind v4 새 기능

**유용한 도구**:
- [Tailwind UI](https://tailwindui.com/) - 프리미엄 컴포넌트 (유료)
- [Headless UI](https://headlessui.com/) - 무료 Headless 컴포넌트

---

### TanStack Query

**공식 문서**: https://tanstack.com/query/latest

**주요 학습 자료**:
- [Overview](https://tanstack.com/query/latest/docs/react/overview) - 개요
- [Quick Start](https://tanstack.com/query/latest/docs/react/quick-start) - 빠른 시작
- [Queries](https://tanstack.com/query/latest/docs/react/guides/queries) - 쿼리 가이드
- [Mutations](https://tanstack.com/query/latest/docs/react/guides/mutations) - 뮤테이션 가이드
- [Polling](https://tanstack.com/query/latest/docs/react/guides/window-focus-refetching) - 폴링 가이드

**심화 학습**:
- [Optimistic Updates](https://tanstack.com/query/latest/docs/react/guides/optimistic-updates)
- [Infinite Queries](https://tanstack.com/query/latest/docs/react/guides/infinite-queries)
- [Query Invalidation](https://tanstack.com/query/latest/docs/react/guides/query-invalidation)

---

### React Router

**공식 문서**: https://reactrouter.com/

**주요 학습 자료**:
- [Tutorial](https://reactrouter.com/en/main/start/tutorial) - React Router 튜토리얼
- [Route](https://reactrouter.com/en/main/route/route) - 라우트 설정
- [Hooks](https://reactrouter.com/en/main/hooks/use-navigate) - useNavigate, useParams 등

---

### React Hook Form

**공식 문서**: https://react-hook-form.com/

**주요 학습 자료**:
- [Get Started](https://react-hook-form.com/get-started) - 시작하기
- [API](https://react-hook-form.com/docs) - API 레퍼런스
- [TypeScript](https://react-hook-form.com/ts) - TypeScript 지원

**Zod 통합**:
- [Zod Resolver](https://github.com/react-hook-form/resolvers#zod) - Zod 유효성 검증 통합

---

### Zod

**공식 문서**: https://zod.dev/

**주요 학습 자료**:
- [Basic Usage](https://zod.dev/?id=basic-usage) - 기본 사용법
- [Primitives](https://zod.dev/?id=primitives) - 기본 타입
- [Objects](https://zod.dev/?id=objects) - 객체 스키마
- [Errors](https://zod.dev/?id=error-handling) - 에러 핸들링

**유용한 패턴**:
- [Type Inference](https://zod.dev/?id=type-inference) - 타입 추론
- [Custom Validators](https://zod.dev/?id=custom) - 커스텀 유효성 검증

---

### Vitest

**공식 문서**: https://vitest.dev/

**주요 학습 자료**:
- [Getting Started](https://vitest.dev/guide/) - 시작하기
- [Features](https://vitest.dev/guide/features.html) - Vitest 기능
- [API](https://vitest.dev/api/) - API 레퍼런스
- [UI Mode](https://vitest.dev/guide/ui.html) - UI 모드

**테스트 라이브러리**:
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/) - React 컴포넌트 테스트
- [user-event](https://testing-library.com/docs/user-event/intro/) - 사용자 이벤트 시뮬레이션

---

### Storybook

**공식 문서**: https://storybook.js.org/

**주요 학습 자료**:
- [Tutorial](https://storybook.js.org/tutorials/intro-to-storybook/react/en/get-started/) - Storybook 튜토리얼
- [Writing Stories](https://storybook.js.org/docs/react/writing-stories/introduction) - 스토리 작성
- [Addons](https://storybook.js.org/docs/react/essentials/introduction) - 애드온 활용

---

## 보안 및 테스팅

### OWASP

**OWASP Top 10**: https://owasp.org/www-project-top-ten/

**주요 취약점**:
1. Broken Access Control
2. Cryptographic Failures
3. Injection (SQL, XSS)
4. Insecure Design
5. Security Misconfiguration
6. Vulnerable and Outdated Components
7. Identification and Authentication Failures
8. Software and Data Integrity Failures
9. Security Logging and Monitoring Failures
10. Server-Side Request Forgery (SSRF)

**DAST 관련**:
- [OWASP ZAP](https://www.zaproxy.org/) - 오픈소스 DAST 도구
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/) - 웹 보안 테스팅 가이드

---

### TDD (Test-Driven Development)

**추천 도서**:
- [Test Driven Development: By Example](https://www.oreilly.com/library/view/test-driven-development/0321146530/) - Kent Beck
- [Growing Object-Oriented Software, Guided by Tests](https://www.oreilly.com/library/view/growing-object-oriented-software/9780321574442/)

**온라인 자료**:
- [TDD 실천법과 도구](https://repo.yona.io/doortts/blog/issue/1) - 한국어 가이드
- [Test-Driven Development with Python](https://www.obeythetestinggoat.com/) - 무료 온라인 책

---

## 개발 도구

### Git

**공식 문서**: https://git-scm.com/doc

**주요 학습 자료**:
- [Pro Git Book](https://git-scm.com/book/en/v2) - 무료 온라인 책
- [Conventional Commits](https://www.conventionalcommits.org/) - 커밋 메시지 규칙
- [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow) - 브랜치 전략

---

### Docker

**공식 문서**: https://docs.docker.com/

**주요 학습 자료**:
- [Get Started](https://docs.docker.com/get-started/) - Docker 시작하기
- [Compose](https://docs.docker.com/compose/) - Docker Compose 가이드
- [Best Practices](https://docs.docker.com/develop/dev-best-practices/) - 베스트 프랙티스

---

### VS Code

**공식 문서**: https://code.visualstudio.com/docs

**추천 확장**:
- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)
- [ESLint](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint)
- [Prettier](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)
- [Tailwind CSS IntelliSense](https://marketplace.visualstudio.com/items?itemName=bradlc.vscode-tailwindcss)

---

## 학습 자료

### 아키텍처 패턴

**추천 도서**:
- [Clean Architecture](https://www.oreilly.com/library/view/clean-architecture-a/9780134494272/) - Robert C. Martin
- [Domain-Driven Design](https://www.oreilly.com/library/view/domain-driven-design-tackling/0321125215/) - Eric Evans
- [Patterns of Enterprise Application Architecture](https://www.martinfowler.com/books/eaa.html) - Martin Fowler

**온라인 자료**:
- [Atomic Design](https://atomicdesign.bradfrost.com/) - Brad Frost (무료)
- [Refactoring Guru](https://refactoring.guru/) - 디자인 패턴

---

### 성능 최적화

**React 성능**:
- [React Performance Optimization](https://react.dev/learn/render-and-commit) - 공식 문서
- [Web Vitals](https://web.dev/vitals/) - 웹 성능 지표

**Backend 성능**:
- [PostgreSQL Performance Tips](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [FastAPI Performance](https://fastapi.tiangolo.com/deployment/server-workers/)

---

### 커뮤니티

**Discord/Slack**:
- [FastAPI Discord](https://discord.gg/fastapi)
- [Reactiflux Discord](https://www.reactiflux.com/) - React 커뮤니티

**Reddit**:
- [r/Python](https://www.reddit.com/r/Python/)
- [r/reactjs](https://www.reddit.com/r/reactjs/)
- [r/typescript](https://www.reddit.com/r/typescript/)

**한국 커뮤니티**:
- [파이썬 한국 사용자 모임](https://www.facebook.com/groups/pythonkorea)
- [React Korea](https://www.facebook.com/groups/react.ko)

---

### 뉴스레터

**Backend**:
- [Python Weekly](https://www.pythonweekly.com/)
- [FastAPI Newsletter](https://fastapi.tiangolo.com/newsletter/)

**Frontend**:
- [React Newsletter](https://reactnewsletter.com/)
- [TypeScript Weekly](https://typescript-weekly.com/)
- [Frontend Focus](https://frontendfoc.us/)

---

### YouTube 채널

**Backend**:
- [Corey Schafer (Python)](https://www.youtube.com/@coreyms)
- [ArjanCodes (Python Architecture)](https://www.youtube.com/@ArjanCodes)

**Frontend**:
- [Jack Herrington](https://www.youtube.com/@jherr) - React/TypeScript
- [Theo - t3.gg](https://www.youtube.com/@t3dotgg) - Full Stack

**보안**:
- [LiveOverflow](https://www.youtube.com/@LiveOverflow) - 웹 보안
- [PwnFunction](https://www.youtube.com/@PwnFunction) - 보안 개념

---

### 블로그

**Backend**:
- [Real Python](https://realpython.com/)
- [Full Stack Python](https://www.fullstackpython.com/)

**Frontend**:
- [Kent C. Dodds](https://kentcdodds.com/blog) - React/Testing
- [Josh W. Comeau](https://www.joshwcomeau.com/) - CSS/React
- [Dan Abramov (Overreacted)](https://overreacted.io/) - React 내부 구조

---

## EAZY 프로젝트 관련 문서

- [프로젝트 개요](PROJECT_OVERVIEW.md)
- [기술 스택](TECH_STACK.md)
- [프로젝트 구조](PROJECT_STRUCTURE.md)
- [아키텍처](ARCHITECTURE.md)
- [에이전트 시스템](AGENT_SYSTEM.md)
- [용어집](GLOSSARY.md)
- [빠른 시작 가이드](../QUICK_START.md)
- [API 명세](../api_spec.md)
- [데이터베이스 스키마](../db_schema.md)
- [코딩 컨벤션](../coding_convention.md)

---

[← 메인 문서로 돌아가기](../README.md)

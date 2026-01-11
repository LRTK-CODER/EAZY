# EAZY 프로젝트 문서

> AI 기반 DAST (Dynamic Application Security Testing) 도구

**EAZY**는 LLM을 활용해 웹 애플리케이션의 비즈니스 로직 취약점을 탐지합니다.

**버전**: 0.1.0 (MVP) | **최종 업데이트**: 2026-01-11

---

## 기술 스택

```
Backend:  Python 3.12 + FastAPI + SQLModel + PostgreSQL + Redis + Playwright
Frontend: React 19 + TypeScript + Vite + TailwindCSS + shadcn/ui + TanStack Query
```

---

## 문서 가이드

| 문서 | 설명 |
|------|------|
| [QUICK_START.md](./QUICK_START.md) | 5분 설정 가이드 |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 시스템 아키텍처, 기술 스택, 프로젝트 구조 |
| [DEVELOPMENT.md](./DEVELOPMENT.md) | TDD, 개발 가이드, Git 워크플로우, 배포 |
| [reference/api_spec.md](./reference/api_spec.md) | REST API 명세 |
| [reference/db_schema.md](./reference/db_schema.md) | 데이터베이스 설계 |
| [reference/coding_convention.md](./reference/coding_convention.md) | 코딩 규약 |
| [reference/GLOSSARY.md](./reference/GLOSSARY.md) | 용어집 |

---

## 필수 규칙

1. **TDD 필수**: RED → GREEN → REFACTOR
2. **UV 필수**: `uv run` (pip 사용 금지)
3. **Type Hint 필수**: mypy (Backend), TypeScript strict (Frontend)
4. **Conventional Commits**: `feat:`, `fix:`, `test:` 등

---

## 테스트 현황

| 영역 | 테스트 | 상태 |
|------|--------|------|
| Backend | 30+ | 100% 통과 |
| Frontend | 168개 | 100% 통과 |

---

## 라이선스

Apache License 2.0

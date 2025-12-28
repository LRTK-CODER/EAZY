# API Specification

## 1. Overview
EAZY Backend API는 **FastAPI**로 구축되었으며 **RESTful** 원칙을 따릅니다.
모든 데이터는 JSON 형식으로 주고받습니다.

*   **Base URL**: `http://localhost:8000`
*   **API Prefix**: `/api/v1`
*   **Documentation**: Swagger UI (`/docs`) 및 ReDoc (`/redoc`) 제공

## 2. Interactive Documentation (Swagger UI)
본 프로젝트는 **Code-First** 방식으로 API 명세를 관리합니다.
가장 정확한 최신 명세는 서버 실행 후 **Swagger UI**를 통해 확인할 수 있습니다.

### 실행 방법
```bash
cd backend
uv run uvicorn app.main:app --reload
```
브라우저에서 [http://localhost:8000/docs](http://localhost:8000/docs) 접속.

## 3. Key Resources

### 3.1. Projects (`/api/v1/projects`)
프로젝트 생성 및 조회.
*   `POST /`: 프로젝트 생성
*   `GET /`: 프로젝트 목록 조회
*   `GET /{id}`: 프로젝트 상세 조회

### 3.2. Targets (`/api/v1/projects/{id}/targets`)
프로젝트 내 진단 대상(URL) 관리.
*   `POST /`: 타겟 등록
*   `GET /`: 타겟 목록 조회
*   `DELETE /{target_id}`: 타겟 삭제
*   `PATCH /{target_id}`: 타겟 정보 수정
*   `POST /{target_id}/scan`: **스캔(크롤링) 작업 트리거**

### 3.3. Tasks (`/api/v1/tasks`)
비동기 작업 상태 및 결과 조회.
*   `GET /{id}`: 작업 상태 조회 (Pending, Running, Completed, Failed)
*   `GET /{id}/assets`: 작업 결과(식별된 자산) 조회

### 3.4. System
*   `GET /health`: 서버 상태 확인

## 4. Error Handling
*   HTTP 422: Validation Error (Pydantic)
*   HTTP 404: Resource Not Found
*   HTTP 500: Internal Server Error

## 5. Data Models
자세한 Request/Response 모델(Schema)은 Swagger UI의 **Schemas** 섹션을 참고하십시오.

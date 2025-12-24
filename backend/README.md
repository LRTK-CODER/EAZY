# EAZY Backend

## 1. Setup (using UV)

```bash
cd backend
# Install dependencies
uv sync
```

## 2. Infrastructure (Docker)
Start the database and Redis containers:
```bash
cd docker
docker compose up -d
cd ..
```

## 3. Configuration
Create a `.env` file in the `backend` directory:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/eazy_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your_secret_key
```

## 4. Running Tests
```bash
uv run pytest
```

## 5. Running Server
```bash
uv run uvicorn app.main:app --reload
```

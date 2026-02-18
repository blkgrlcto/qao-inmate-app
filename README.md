# QAO Inmate App

Monorepo containing the web frontend, API service, and infrastructure for local development.

## Project Structure

```
├── apps/
│   └── web/          # Next.js 14+ (App Router, TypeScript, Tailwind)
├── services/
│   └── api/          # FastAPI (uvicorn, pydantic, SQLAlchemy)
├── infra/            # Docker Compose (postgres, minio, api, web)
└── README.md
```

## Prerequisites

- **Node.js** 18.17+ (for Next.js)
- **Python** 3.10+ (for FastAPI)
- **Docker** & **Docker Compose** (for full stack)

## Quick Start (Docker)

From the project root:

```bash
cd infra

# 1. Start Postgres
docker compose up -d postgres

# 2. Run migrations and seed (first-time setup)
docker compose run --rm -e DB_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/qao_inmate api alembic upgrade head
docker compose run --rm -e DB_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/qao_inmate api python -m scripts.seed

# 3. Start API and web
docker compose up -d api web
```

- Web: http://localhost:3000
- API: http://localhost:8000
- API docs: http://localhost:8000/docs

Demo login: **attorney@demo.local** / **demo123**

## Development Setup

### Option 1: Local development (recommended for active coding)

Run from project root (`qao-inmate-app/`).

#### 1. Start dependencies (Postgres + MinIO)

```bash
cd infra
docker compose up -d postgres minio
```

#### 2. Database setup (first-time)

```bash
cd services/api
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .env has DB_URL for localhost by default

alembic upgrade head
python -m scripts.seed
```

#### 3. Run the API

```bash
cd services/api
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API: http://localhost:8000 | Docs: http://localhost:8000/docs

#### 4. Run the web app (new terminal)

```bash
cd apps/web
npm install
npm run dev
```

Web: http://localhost:3000

### Option 2: Full Docker stack

```bash
cd infra
docker compose up -d postgres
docker compose run --rm -e DB_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/qao_inmate api alembic upgrade head
docker compose run --rm -e DB_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/qao_inmate api python -m scripts.seed
docker compose up -d --build api web
```

- Web: http://localhost:3000
- API: http://localhost:8000
- Postgres: localhost:5432
- MinIO: http://localhost:9000 (API), http://localhost:9001 (console)

### Option 3: API + Web only (external Postgres/MinIO)

Run the apps locally with your own Postgres/MinIO. Set `DB_URL` in `services/api/.env` and `NEXT_PUBLIC_API_URL` in `apps/web/.env.local` if needed.

## Auth

- **Login:** `POST /api/v1/auth/login` with form fields `username` (email) and `password`
- **Current user:** `GET /api/v1/auth/me` with `Authorization: Bearer <token>`

Demo accounts: attorney@demo.local, paralegal@demo.local, inmate@demo.local (all: demo123)

## Database

- Host: localhost (or `postgres` in Docker)
- Port: 5432
- User: postgres
- Password: postgres
- Database: qao_inmate

**Migrations & seed (Docker):** Use the commands in Quick Start or Option 2. Required before first login.

**Migrations & seed (local):** Use the commands in Option 1 step 2. Requires venv activated and deps installed.

## Useful Commands

| Command | Description |
|---------|-------------|
| `cd infra && docker compose up -d` | Start all services |
| `cd infra && docker compose down` | Stop all services |
| `cd apps/web && npm run dev` | Next.js dev server |
| `cd services/api && source .venv/bin/activate && uvicorn app.main:app --reload` | FastAPI dev server |

## MinIO (Object Storage)

- API: http://localhost:9000
- Console: http://localhost:9001 (minioadmin / minioadmin)

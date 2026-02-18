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

## Development Setup

### Option 1: Local development (recommended for active coding)

#### 1. Start dependencies (Postgres + MinIO)

```bash
cd infra
docker compose up -d postgres minio
```

#### 2. Run the API

```bash
cd services/api
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # adjust DATABASE_URL if needed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be at **http://localhost:8000**

- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs
- MinIO console: http://localhost:9001 (minioadmin / minioadmin)

#### 3. Run the web app

```bash
cd apps/web
npm install
npm run dev
```

Web app will be at **http://localhost:3000**

### Option 2: Full Docker stack

```bash
cd infra
docker compose up -d --build
```

- Web: http://localhost:3000  
- API: http://localhost:8000  
- Postgres: localhost:5432  
- MinIO: http://localhost:9000 (API), http://localhost:9001 (console)

### Option 3: API + Web only (external Postgres/MinIO)

If you have Postgres and MinIO elsewhere, run the apps locally with appropriate `.env` values:

```bash
# services/api/.env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# apps/web - set NEXT_PUBLIC_API_URL in .env.local if different from localhost:8000
```

## Useful Commands

| Command | Description |
|---------|-------------|
| `cd apps/web && npm run dev` | Start Next.js dev server with hot reload |
| `cd apps/web && npm run build` | Build Next.js for production |
| `cd services/api && uvicorn app.main:app --reload` | Start FastAPI with auto-reload |
| `cd infra && docker compose up -d` | Start all services in background |
| `cd infra && docker compose down` | Stop all services |

## Database

Default Postgres credentials:

- Host: localhost (or `postgres` when in Docker)
- Port: 5432
- User: postgres
- Password: postgres
- Database: qao_inmate

### Migrations (Alembic)

```bash
cd services/api
# With DB running (e.g. docker compose up -d postgres)
alembic upgrade head
```

### Seed (demo data)

```bash
cd services/api
alembic upgrade head   # run migrations first
python -m scripts.seed
```

Creates: 1 attorney, 1 paralegal, 1 inmate, 1 demo case shared to all.

- attorney@demo.local / demo123
- paralegal@demo.local / demo123
- inmate@demo.local / demo123

## MinIO (Object Storage)

- API endpoint: http://localhost:9000  
- Console: http://localhost:9001  
- Default credentials: minioadmin / minioadmin  

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A test case management platform with a FastAPI backend, React/TypeScript frontend, PostgreSQL database, and Celery task queue for async test execution.

## Commands

### Backend
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run dev server
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Database migrations
cd backend && alembic upgrade head
cd backend && alembic revision --autogenerate -m "description"

# Run Celery worker
cd backend && celery -A app.tasks.celery_app worker --loglevel=info
```

### Frontend
```bash
cd frontend && npm install
npm run dev      # dev server on port 3000
npm run build    # production build
```

## Architecture

### Stack
- **Backend**: FastAPI + SQLAlchemy (async) + PostgreSQL + Celery + Redis
- **Frontend**: React 18 + TypeScript + Vite + Ant Design + Axios
- **Auth**: JWT (HS256, 24h expiry) stored in localStorage

### Key Config
All settings are in `backend/app/core/config.py` via pydantic-settings — override with environment variables:
- `DATABASE_URL` — `postgresql+asyncpg://postgres:postgres@db:5432/test_platform`
- `SYNC_DATABASE_URL` — used by Alembic migrations only
- `SECRET_KEY` — defaults to `"change-me-in-production"`, must be overridden in prod
- `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` — Redis databases 1 and 2

### Data Model
```
User (roles: ADMIN/MANAGER/TESTER/VIEWER)
Project → Environment (base_url, variables)
        → TestSuite → TestCase (priority P0-P3, script_path)
TestExecution → TestResult (per-case: PENDING/RUNNING/PASSED/FAILED/ERROR/SKIPPED)
```
All PKs are UUIDs. Roles are defined but not yet enforced in API endpoints.

### Test Execution Flow
1. `POST /api/v1/executions` creates `TestExecution` + `TestResult` rows (PENDING)
2. Enqueues Celery task `run_execution` (broker: Redis db 1)
3. Worker runs each `TestCase.script_path` via subprocess (300s timeout), captures stdout/stderr
4. Updates `TestResult` status and aggregates back to `TestExecution`

### Frontend → Backend
- Vite dev proxy: `/api` → `http://backend:8000`
- Axios base URL: `/api/v1`; Bearer token auto-injected from `localStorage`; 401 redirects to `/login`
- Path alias `@` maps to `frontend/src/`

### Docker
Services expected: `db` (PostgreSQL :5432), `redis` (:6379), `backend` (:8000). No `docker-compose.yml` exists yet — `docker/nginx/` is also empty.

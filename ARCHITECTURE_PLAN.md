# MergenLite — Architecture Overhaul Plan

> **Status:** In Progress  
> **Last Updated:** 2026-02-14  
> **Goal:** Remove Supabase/Streamlit dependencies; adopt React + FastAPI + Docker PostgreSQL

---

## ✅ Completed Steps

### Step 1: Folder Structure & Legacy Cleanup
- [x] Legacy Streamlit/NiceGUI files moved to `legacy_files/`
  - `app.py`, `app_nicegui*.py`, `mergenlite_app.py`
  - `test_streamlit.py`, `test_nicegui_simple.py`
  - `theme.css`, `theme_loader.py`, `backend_utils.py`
  - `guided_analysis.py`, `mergenlite_ui_components.py`
  - `Dockerfile` (Streamlit), `streamlit.Dockerfile`
  - `temp_*` folders, `Mergenliteuiuxtasarmcopy/`
- [x] Duplicate model files deprecated
  - `models_unified.py` → moved to `legacy_files/`
  - `mergenlite_models.py` → replaced with compatibility shim (re-exports from `db_models.py`)
- [x] Root agents (`agents/`) copied into `mergen/api/app/agents/`

### Step 2: Database & Docker Configuration
- [x] `docker-compose.yml` (root) — uses `pgvector/pgvector:pg15` image
  - db healthcheck with `pg_isready`
  - Backend depends on db with `condition: service_healthy`
  - Default DB name: `mergenlite`
- [x] `mergen/docker-compose.yml` — cleaned, removed Streamlit/Redis/worker
- [x] `mergen/api/app/db.py` — modernized
  - Connection pool: `pool_size=10`, `max_overflow=20`, `pool_pre_ping`, `pool_recycle=300`
  - `get_db()` for FastAPI, `get_db_session()` context manager for scripts
  - `init_pgvector()` — enables pgvector extension on startup
  - `check_db_health()` — SELECT 1 probe
- [x] `mergen/api/app/config.py` — cleaned up
  - Single `.env` loading, no duplicate `model_post_init` hacks
  - `database_url` property: DATABASE_URL env > individual vars
  - Added `is_production`, `log_level`, LLM settings
- [x] `.env` files organized with `DATABASE_URL`, `PIPELINE_NOTIFICATION_EMAIL`
- [x] Alembic `env.py` — all models imported for autogenerate (including Hotel)

### Step 3: Unified Data Model
- [x] `mergen/api/app/models/db_models.py` = **Single Source of Truth**
  - 20+ tables: Opportunity, Attachments, Analysis, Jobs, Hotels, Agents, Documents, RAG, Meta
  - `VectorChunk.embedding` → native pgvector `Vector(1536)` (falls back to JSON)
  - Added `token_count` column for cost tracking
- [x] `models/__init__.py` — all models re-exported (Hotel was missing, now fixed)
- [x] Compatibility shim at root (`mergenlite_models.py`) for legacy scripts

### Step 4: Backend (FastAPI) Workflows
- [x] `mergen/api/app/main.py` — rewritten
  - Clean startup: migrations → pgvector init
  - `/health` includes DB status
  - Version bumped to `2.0.0`
  - Logging instead of print()
- [x] `mergen/api/app/deps.py` — Simple HTTP Basic auth
  - Users from `AUTH_USER_1=admin:pass` env vars
  - Falls back to demo user when no auth header (gradual migration)
  - `require_admin` guard
- [x] `routes/health.py` — checks DB connectivity

### Step 5: Frontend (React/Vite) Integration
- [x] `frontend/src/api/client.ts` — enhanced
  - 60s timeout (for long pipelines)
  - Optional Basic auth from localStorage
  - Dev-only logging
  - `setCredentials()` / `clearCredentials()` helpers
- [x] `opportunities.ts`, `pipeline.ts`, `dashboard.ts` — already well-structured ✓

### Step 6: Internal RAG & Vector DB
- [x] pgvector enabled via `pgvector/pgvector:pg15` Docker image
- [x] `mergen/api/app/services/llm/rag.py` — rewritten
  - OpenAI `text-embedding-3-small` (1536 dims), falls back to sentence-transformers
  - `chunk_text()` — overlapping word-based chunking
  - `ingest_document()` — chunk → embed → INSERT
  - `search_documents()` — pgvector `<=>` cosine distance (falls back to numpy)
  - Higher-level: `retrieve_context()`, `find_similar_chunks()`, `build_context_for_requirement()`

---

## 🔄 Remaining Tasks

### Migration & Schema Sync
- [ ] Generate fresh Alembic migration: `alembic revision --autogenerate -m "v2.0 unified schema"`
- [ ] Test migration against clean database
- [ ] Test migration against existing database (backward compat)

### Auth UI
- [ ] Add Login page to React frontend
- [ ] Wire `setCredentials()` to login form
- [ ] Protect routes in frontend with auth check

### Local Dependency Cleanup
- [ ] Remove any `D:/RFQ` references from pipeline code
- [ ] Ensure all agent imports resolve within project tree

### Testing
- [ ] `docker compose up --build` smoke test
- [ ] SAM sync end-to-end test
- [ ] Pipeline analysis end-to-end test
- [ ] PDF generation test
- [ ] RAG ingest + search test

### Production Readiness
- [ ] Cloud Run deployment config update
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Monitoring / structured logging

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
│              React / Vite / nginx                │
│             localhost:3000 → :80                  │
└──────────────────┬──────────────────────────────┘
                   │ HTTP (axios)
                   ▼
┌─────────────────────────────────────────────────┐
│                   Backend                        │
│              FastAPI / Uvicorn                    │
│             localhost:8000 → :8080                │
│                                                  │
│  Routes: opportunities, pipeline, dashboard,     │
│          jobs, proxy, communications             │
│  Services: SAM sync, pipeline, PDF gen,          │
│            mail, RAG, hotel matcher              │
│  Agents: SOW analyzer, reviewer, hotel matcher   │
│  Auth: HTTP Basic (2-user)                       │
└──────────────────┬──────────────────────────────┘
                   │ SQLAlchemy
                   ▼
┌─────────────────────────────────────────────────┐
│                  Database                        │
│          PostgreSQL 15 + pgvector                │
│             localhost:5432                        │
│                                                  │
│  20+ tables: opportunities, attachments,         │
│  analysis_results, hotels, documents,            │
│  vector_chunks (RAG), agent_runs, ...            │
└─────────────────────────────────────────────────┘
```

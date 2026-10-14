# AI Project Architect

AI Project Architect is a planned workspace for turning a software idea into a reviewable architecture. The intended workflow separates user requirements, AI suggestions, and explicit assumptions, then produces validated design artifacts and an editable system diagram.

**Current status: Phase 1 foundation.** This repository contains an API and frontend shell, database schema setup, health checks, tests, and architecture documentation. Project workflows and AI generation are **not implemented yet**. The UI reports service health; it does not display fabricated project data.

**Phase 1.5 verification (2026-10-14):** 26 backend tests passed against PostgreSQL 16.14, including seven database integration tests; eight frontend tests, type checks, lint, formatting, and the production build passed. Migrations and database outage/restart recovery were executed locally. Docker is unavailable on the verification host: container builds, Compose semantic validation, and container restart behavior remain unverified. See the [verification report and Docker checklist](docs/verification-phase-1-5.md).

## Problem and MVP

Early software architecture work often mixes requirements with guesses and loses the reasons behind technology choices. The MVP will let a user create a project, review extracted requirements and clarification questions, run a deterministic mock architecture workflow, and save and inspect the resulting graph. See [the architecture plan](docs/architecture.md) and [delivery plan](docs/phases.md).

This is a single-operator portfolio application at present. It has no authentication or tenant isolation and must not be exposed as a multi-user service.

## Stack

- Backend: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL.
- Frontend: React, TypeScript, Vite, Tailwind CSS, TanStack Query, React Router. React Flow is planned for Phase 2.
- Infrastructure: Docker Compose for local Postgres, API, and frontend; GitHub Actions checks.
- AI: provider boundary, deterministic mock provider, and OpenAI-compatible provider are planned for later phases.

## Repository map

```text
backend/       API, settings, database model, migration, tests
frontend/      React application shell
docs/          system design, decisions, delivery phases
.github/       CI workflow
compose.yaml   local services
```

## Local development

Requirements: Python 3.12 or 3.13, Node.js 20+, npm, and PostgreSQL 16. Docker Compose can supply PostgreSQL or run the whole stack. Copy `.env.example` to `.env` and set a local password. Values in the example are for local development only. The backend constructs its connection from `POSTGRES_*` fields, preserving special characters in passwords. An optional `DATABASE_URL` overrides those fields for a host-run backend; URL credentials must be percent-encoded. Compose always supplies separate credentials and sets the backend database host to `db`.

Environment-file parsing still applies: quote values containing `#` and avoid `${...}` sequences in `.env` passwords because Python dotenv can interpolate them. Direct process environment variables bypass dotenv file interpolation.

```bash
cp .env.example .env
docker compose up -d db
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e './backend[dev]'
alembic -c backend/alembic.ini upgrade head
uvicorn architect.main:app --app-dir backend --reload --no-access-log
```

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`. API docs are at `http://localhost:8000/docs`; `GET /health/live` checks the process and `GET /health/ready` checks PostgreSQL and the required project columns without reading project records. A missing schema or failed connection returns a generic 503. Readiness does not replace `alembic check` or verify every constraint.

Vite reads the repository-root `.env` (`envDir: '..'`). The browser uses `VITE_API_BASE_URL`, defaulting to `http://localhost:8000`. Only variables prefixed `VITE_` become visible in the browser. Never put credentials there. This URL is baked into the production build; changing it requires rebuilding the frontend image.

The API restricts CORS to explicit origins and creates a new request ID for each handled request. Its JSON request logs contain the route template, status, and duration; query strings and unknown raw paths are omitted. `--no-access-log` prevents Uvicorn's separate access log from recording query strings.

To run all services in containers:

```bash
docker compose up --build
```

## Checks

```bash
python -m pytest backend/tests
ruff check backend
ruff format --check backend
cd frontend && npm run typecheck && npm run test && npm run build
```

The CI workflow is configured to run these checks, a PostgreSQL migration round trip, and a separate Compose build/start/restart job. It has not been run remotely in this session.

Database tests require a **disposable, password-authenticated PostgreSQL database**. They insert and roll back test rows and briefly create an isolated test schema. Set `TEST_DATABASE_URL` to its percent-encoded URL, then run:

```bash
DATABASE_URL="$TEST_DATABASE_URL" alembic -c backend/alembic.ini upgrade head
DATABASE_URL="$TEST_DATABASE_URL" alembic -c backend/alembic.ini check
RUN_DB_TESTS=1 python -m pytest backend/tests -q
```

Without `RUN_DB_TESTS=1`, database tests skip. With the flag but no explicit `TEST_DATABASE_URL`, pytest stops with a configuration error rather than falling back to the development database. Unit tests use an isolated configuration.

## Evaluation and security

The planned evaluation suite uses a fixed set of project descriptions and tests requirement coverage, graph integrity, API and database consistency, and workflow completion. Mock scores will be labeled as mock results; live provider performance will be evaluated separately. No evaluation metrics exist yet.

Descriptions and future provider responses are untrusted data. The design calls for bounded inputs, typed outputs, validated graph edges, safe text rendering, timeouts, and explicit provider errors. Generated SQL or code will remain exportable artifacts and will never run automatically. Until authentication, rate limiting, and isolation are added, use only in a trusted local environment. See [SECURITY.md](SECURITY.md).

## Screenshots

No screenshots have been captured yet.

## Roadmap and limitations

The [phase plan](docs/phases.md) lists the delivery order and acceptance gates. The current application has no project CRUD, AI analysis, graph editor, exports, or user accounts. Docker runtime verification is still pending; the [verification report](docs/verification-phase-1-5.md) records exactly what ran.

Contributions and security reporting are described in [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md). Licensed under [MIT](LICENSE).

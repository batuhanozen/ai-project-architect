# Phase 1.5 engineering verification

Date: 2026-10-14. Scope: verify and harden the existing foundation. No Phase 2 project features, agents, or provider integration were added. Existing uncommitted files were preserved. No commit, push, deployment, or remote Actions run was performed.

## Findings and changes

| Finding | Change and evidence |
| --- | --- |
| `SELECT 1` returned readiness 200 before migrations | Reproduced against a fresh PostgreSQL database. Readiness now selects required project columns with `LIMIT 0`; missing schema returns 503. Verified before and after migration. |
| No explicit database connection, pool-wait, or query limits | Added bounded settings, a finite pool, PostgreSQL statement timeout, and shutdown disposal. A slow query is cancelled in an integration test; the connection works after rollback. |
| Compose concatenated credentials into a URL | Separate `POSTGRES_*` fields now use SQLAlchemy `URL.create`. A generated password containing `@:/%` connected successfully to real PostgreSQL. Optional `DATABASE_URL` remains supported for host workflows. |
| Settings accepted arbitrary database URLs and CORS strings | Restricted the driver to `postgresql+psycopg`, validated origins and timeout ranges, and masked credentials in settings/errors. Tests cover invalid input. |
| Logging recorded raw paths; unhandled exceptions bypassed request logging | Log route templates, generate request IDs, sanitize unexpected 500 responses, and disable Uvicorn access logs in documented/container startup commands. Real HTTP checks confirm query-token/password redaction and graceful shutdown. |
| Root `.env` was not loaded by the frontend | Vite now explicitly reads the repository-root environment directory; only `VITE_*` values are browser configuration. Normalize a trailing slash in the API base URL and sanitize malformed JSON errors. |
| Both Docker runtime stages defaulted to root; frontend had no healthcheck | Added non-root runtime users, read-only application filesystems, temporary writable storage, capability restrictions, frontend healthcheck, and restart policies. Backend startup uses `exec` so Uvicorn receives termination signals. **Static review only; runtime unverified.** |
| CI did not test Compose or migration rollback/schema drift | Added a disposable migration round trip, `alembic check`, an explicit test database URL, and a Compose verification job. **Workflow written, not run remotely.** |

The initial project model and migration agreed: UUID primary key, 160-character name, non-null description, and timezone-aware timestamps with server defaults. No schema migration change was needed. UUID generation and `updated_at` changes are SQLAlchemy-managed; direct SQL writers must supply IDs and manage updates themselves.

## Executed checks

Verification used Python 3.13.3, PostgreSQL 16.14 (Homebrew), Node.js 20.20.2, and npm 8.15.0. The system-default Node.js 16 was not used for frontend checks. CI targets Python 3.12; that exact runtime was not executed locally.

| Check | Result |
| --- | --- |
| Ruff lint and format | Passed after fixes |
| Backend pytest with `RUN_DB_TESTS=1` and an explicit `TEST_DATABASE_URL` | **26 passed, 0 failed, 0 skipped**; includes seven PostgreSQL integration tests |
| PostgreSQL migration `upgrade head`, `downgrade base`, `upgrade head` | Passed on an isolated disposable cluster and database |
| Alembic `current` and `check` | Head is `0001_create_projects`; no schema drift detected |
| Project table inspection and round-trip insert/select | Passed; column types, nullability, primary key, timestamp defaults and required description checked |
| PostgreSQL authentication failure and absent schema | Both return generic readiness 503; no credentials exposed |
| Real HTTP process with database outage/restart | Readiness 200 → 503 → 200; liveness remains 200 while PostgreSQL is stopped; same API process recovers |
| Real HTTP CORS, request ID, log redaction, graceful shutdown | Passed |
| `npm ci --offline --no-audit --no-fund` | Passed from the committed lockfile using the available local cache |
| Frontend typecheck, Vitest, production build | Passed; **8 tests passed** |
| YAML parsing of Compose and Actions files | Passed; this does **not** validate Compose semantics |
| `git diff --check` | Passed |

PostgreSQL ran on loopback port 55432 in a temporary cluster. A dedicated non-superuser database owner ran migrations and tests. The migration downgrade touched only that disposable database. The HTTP verification used a temporary Uvicorn process on port 18000. Verification processes were stopped after testing.

### Failures encountered and resolved

- The first pytest invocation failed during import: the editable-install `.pth` file had the macOS `hidden` flag. Python 3.13 skips such files. Reinstallation alone did not reliably remove the environment issue. The local flag was cleared and verification subprocesses used `PYTHONPATH=backend` to import this checkout explicitly. This workaround is local, not a repository packaging change. If it recurs, clear the hidden flag on the editable `.pth` file or use `PYTHONPATH=backend python -m pytest backend/tests` after installing dependencies.
- Initial isolated PostgreSQL initialization was blocked by sandbox shared-memory permissions. The same isolated cluster was initialized and tested with approved local process permissions.
- Intermediate lint errors introduced while editing were corrected before final checks.

Starlette emitted a deprecation warning about its httpx test-client integration; React Router emitted v7 future-behavior warnings. They did not fail tests. No dependency vulnerability scan or load test was performed.

## Blocked / untested infrastructure

`docker` is not executable: `/usr/local/bin/docker` points to the absent `/Applications/Docker.app`. The Docker socket is absent. Consequently, none of the following has passed locally:

- Docker Compose semantic validation (`docker compose config`).
- Backend/frontend image builds and image-level package installation.
- Actual nginx startup, non-root permissions, read-only filesystem compatibility, or container healthchecks.
- Compose networking, startup dependency ordering, service logs, or container restart behavior.

PostgreSQL verification used a native server, **not** the `postgres:16-alpine` image. Parsing YAML, generating SQL offline, and writing a CI job do not substitute for these checks.

## Local Docker verification procedure

Run from the repository root after installing and starting Docker with Compose v2. Preserve an existing `.env`; create one only if missing and choose local credentials. A changed password does not update an existing database volume's password.

```bash
[ -f .env ] || cp .env.example .env
docker version
docker compose version
docker compose config --quiet
docker compose build --pull
docker compose up -d --wait --wait-timeout 120
docker compose ps
docker compose exec -T db sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
docker compose exec -T api alembic -c alembic.ini current
docker compose exec -T api alembic -c alembic.ini check
curl --fail http://localhost:8000/health/live
curl --fail http://localhost:8000/health/ready
curl --fail http://localhost:5173/
docker compose exec -T api id
docker compose exec -T frontend id
docker compose logs --no-color --tail=100
docker compose restart db
curl --fail --retry 15 --retry-all-errors --retry-delay 2 http://localhost:8000/health/ready
docker compose restart api frontend
curl --fail --retry 15 --retry-all-errors --retry-delay 2 http://localhost:8000/health/ready
curl --fail --retry 15 --retry-all-errors --retry-delay 2 http://localhost:5173/
docker compose ps
docker compose logs --no-color --tail=100
docker compose down
```

Expect all three services to become healthy, both application runtime users to have nonzero UIDs, readiness to recover, and no startup errors in logs. Open `http://localhost:5173` and confirm both health cards recover. `down` preserves the database volume; do not add `--volumes` to a command against data you want to keep. `restart: unless-stopped` restarts exited containers, not containers merely marked unhealthy.

## Acceptance decision

Application and native PostgreSQL acceptance checks pass. Full Phase 1.5 infrastructure acceptance remains **pending Docker verification**. Phase 2 can technically be developed using the verified native PostgreSQL path, but this review does not grant an unconditional foundation acceptance or recommend closing the infrastructure gate before the Docker checklist passes. No Phase 2 work began.

Remaining limitations: unauthenticated local use, a privileged local Compose database account, floating backend dependency ranges/image tags, no load or vulnerability assessment, and unexecuted remote CI. Automatic migrations on API startup are intended for one local API instance; deployment needs a separate migration step and runtime database role.

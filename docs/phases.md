# Delivery plan

Each phase has a test gate. Completing a phase does not authorize starting the next one.

| Phase | Deliverable | Gate |
| --- | --- | --- |
| 1 Foundation | API and frontend skeleton, Postgres model and migration, health checks, lint, CI, documentation | Tests, static checks, build, and migration apply where runtimes are available |
| 1.5 Verification | Real PostgreSQL migration and failure checks, bounded connections, safe configuration/logging, container hardening | Application and PostgreSQL checks passed; Docker build/start/restart acceptance remains pending; see [report](verification-phase-1-5.md) |
| 2 Functional MVP | Project CRUD, editable requirements, deterministic mock workflow, persisted architecture revisions, basic React Flow graph | API, database, workflow, and browser tests cover the full mock journey |
| 3 AI engineering | Live provider, structured output retries, stateful orchestration where justified, review, tracing, token and cost telemetry, evaluation harness | Fixed mock dataset passes; live runs reported separately |
| 4 Product features | Graph edits, selected component regeneration, ER design, OpenAPI export, roadmap, export and revision history | Artifact validation and round-trip persistence tests |
| 5 Hardening | Auth strategy, rate limits, load checks, security review, deployment guidance | Security and deployment checks documented and executed |

## Technical risks

1. **Model inconsistency:** independent generated artifacts can disagree. Use shared typed state, referential validation, and a review step.
2. **Silent assumptions:** source-tag every requirement and require explicit user review for critical missing facts.
3. **Provider cost and failure:** bounded inputs, timeouts, limited retry policy, clear run status, and cost telemetry.
4. **Graph safety:** backend-generated identifiers and edge validation; frontend renders text rather than provider HTML or JavaScript.
5. **Security gap:** no authentication in the MVP. Limit it to local use and avoid claims of multi-user SaaS readiness.
6. **Toolchain reproducibility:** use compatible dependency ranges and a committed frontend lockfile. Keep CI checks explicit.

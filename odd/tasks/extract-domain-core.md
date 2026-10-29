# Feature: extract-domain-core

Objective: extract a pure, stdlib-only domain core shared by the CLI and the GUI workspace, without changing CLI or API behavior.
Branch: `refactor/extract-domain-core` (slice 1 of the chain domain → API → frontend). Delivery: `ask-on-risk`; forecast ~1,100 authored changed lines, most of it moved code.
Test runner: `.venv/Scripts/python -m unittest discover -s tests -v` (CI: Python 3.9 stdlib-only + 3.12 with backend deps).

## Specs

- **S1** — Domain extraction (user, L2/L3): "La primera tarea de implementación sería refactorizar el script actual para extraer el dominio, manteniendo todas sus pruebas y su funcionamiento por CLI." Accepted proposal: "Primero extraer el dominio puro, compartido por la CLI y la API, con sus tests."
  - Acceptance: business rules (URL normalization, Android URIs, account identity, duplicate detection, consolidation, password reuse, strength heuristics, username masking) live in `backend/password_checker/domain/`, which imports neither FastAPI nor any I/O.
  - Acceptance: `workspace.py` no longer imports `auditar_contrasenas_local`; the CLI and workspace call the same domain functions.
- **S2** — Behavior preserved: "manteniendo todas sus pruebas y su funcionamiento por CLI."
  - Acceptance: every existing test passes unchanged; CLI flags, stdout, stderr, exit codes and generated files are byte-identical to the base commit in a differential check.
  - Acceptance: the CLI remains runnable as `python auditar_contrasenas_local.py ...` on Python 3.9 with no third-party dependencies.
- **S3** — Quality bar (user, L2): "quiero código de alta calidad, reutilizable (dry) y principios solid."
  - Acceptance: no duplicated rule implementations between the CLI and workspace (note merging, Bitwarden row mapping, exclusive file creation, reuse grouping, weak-password rule); the domain has its own unit tests through its public functions.
  - Assumption: layout stays at `backend/password_checker/` (no `src/` move) so `app.py` and API imports are untouched in this slice; `src/` and the API layer belong to the next slice.

## Tasks

| ID | Specs | Route | Status | Evidence |
| --- | --- | --- | --- | --- |
| T1 | S1, S3 | inline | pending | Domain package (credential, urls, strength, accounts, notes, consolidation) + domain tests; CLI consumes it |
| T2 | S1, S2, S3 | inline | pending | Infrastructure (CSV reader, Bitwarden writer, exclusive file creation) + Markdown report + thin CLI shim |
| T3 | S1, S3 | inline | pending | Workspace consumes domain and infrastructure; no import of the root script |
| T4 | S2 | inline | pending | Differential CLI check vs base commit, 3.9 syntax check, docs updated |

Route evidence: no Writer trigger — units are sequential (T2/T3 depend on T1), so the parent works inline.

## Log

- **L1** (2026-10-29, user): "Investiga el repo y dime en qué estado se encuentra"
- **L2** (2026-10-29, user, pasted history): "Nos sirve para empezar. No lo he dicho porque supongo que está claro, pero quiero código de alta calidad, reutilizable (dry) y principios solid. Nivel gurú informático." Approved stack proposal: "La primera tarea de implementación sería refactorizar el script actual para extraer el dominio, manteniendo todas sus pruebas y su funcionamiento por CLI. Después levantaríamos la API y, finalmente, la interfaz gráfica."
- **L3** (2026-10-29, user): "Sí" — to: "¿Empiezo por la extracción del dominio?" after proposing a new branch from `main` and chained PRs (domain → API → frontend).
- **L4** (2026-10-29): Baseline on base `d172802`: 31 tests OK, 0 skipped (venv with backend deps, Python 3.11). No local Python 3.9: syntax is checked with `ast.parse(feature_version=(3, 9))`; CI covers the real 3.9 run.
- **L5** (2026-10-29): Known divergence kept on purpose (behavior-preserving): CLI note prefix "URI Android de origen: " vs workspace "URI Android original: "; reuse grouping keyed by host in the CLI vs canonical URL in the workspace. Unifying them changes output and needs a user decision.

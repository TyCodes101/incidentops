# Verification evidence — October 17, 2026

## Commands and observed results

| Command | Result |
|---|---|
| `python -m pip install -e '.[dev]'` | Installed backend and test dependencies; Alembic and argon2-cffi installed separately during implementation and included in final pyproject |
| `python -m pytest -q` on untouched extracted starter | 7 passed |
| `python -m pytest -q` in completed repository | 23 passed; one upstream Starlette TestClient/httpx deprecation warning |
| `python -m ruff check .` | Passed |
| `python -m alembic upgrade head` | Passed on local SQLite |
| `python -m incidentops.manage demo` | Explicit synthetic seed succeeded; repeated invocation reports no changes |
| `python -m uvicorn incidentops.main:app --host 127.0.0.1 --port 8000` | Started successfully; GET /health returned 200 |
| `npm install` then final locked dependencies | Installed; final audit reports zero vulnerabilities |
| `npm run typecheck` | Passed |
| `npm run lint` | Passed |
| `npm test` | 6 interaction tests passed |
| `npm run build` | Passed; Vite production assets generated |
| `npm audit` | Zero reported vulnerabilities |
| `python tests/browser_smoke.py` (equivalent workspace script executed against running services) | Desktop/mobile workflow passed; no uncaught browser JavaScript errors |

The host has Node 24 and Python 3.14. npm was missing from PATH, so frontend commands used `node <workspace>/work/package/bin/npm-cli.js <command>`. npm was obtained from its official registry. The delivered project uses standard npm commands with a committed package-lock.json. Node 22.12+ is recommended for the selected test runner.

The migrations test creates revision 0001, inserts a legacy incident and audit event, upgrades to head, reruns upgrade, verifies records and tables, downgrades and re-upgrades. API tests cover unauthenticated access, login failure/throttling, CSRF/origin rejection, expiry/logout, Viewer/Analyst restrictions, admin provisioning, assignment validation, incident creation and updates, no-op history, notes, search/filter/sort/pagination, missing/invalid requests, metrics/trends, CSV parsing and limits.

Frontend tests cover login errors, incident creation, server filter queries, loading/failure/retry UI, status PATCH and Viewer controls. They use mocked network responses. The separate browser script verifies the real native frontend/API/SQLite path: sign-in, persisted creation, status/severity/assignment, note, resolve confirmation, search/filter, audit navigation, sample CSV analysis and flag conversion, mobile overflow and sign-out. Screenshots are actual browser captures, not mockups.

## Corrections made while verifying

- Fixed a JSX syntax error and typed test mock signatures found by the production build.
- Updated Vitest after the dependency audit reported vulnerable transitive packages; the final audit is clean.
- Added explicit accessible names to form selects after browser testing exposed ambiguous label matching.
- Fixed mobile navigation overflow and unreadable compressed filter controls.
- Added proper Windows subprocess stdin handling to migration tests and SQLite batch migration foreign-key handling.
- Browser screenshots now wait for the incident queue to finish loading.

## Boundaries

Docker is not installed/on PATH: no container image builds, Compose runtime, or live PostgreSQL acceptance tests were performed. The YAML can be read, but this does not prove Docker execution. GitHub Actions configuration has not run on a remote repository. No push or deployment occurred. No paid resources were created. No benchmark, coverage percentage, or production-readiness claim is made.

The PowerShell launcher is provided for systems with Python and npm installed. Its syntax was parsed locally; the full fresh-venv launcher workflow was not repeated here because the host lacks a normal npm installation. Manual native startup was executed successfully. See SECURITY.md for remaining production hardening gaps.

## Repeat browser verification

With the native API/frontend running and demo explicitly seeded:

```sh
python -m pip install -e '.[browser]'
python -m playwright install chromium
python tests/browser_smoke.py
```

This creates additional fictional cases, writes screenshots under docs/screenshots, and signs out its own browser context. Run it against a disposable demo workspace, not a production database.

# IncidentOps redesign

The interface now centers the analyst's daily work: a triage queue, readable case evidence, recorded decisions and clear ownership. The approved light workbench, slate-blue action, compact Inter typography and restrained geometry are applied throughout.

## What changed

- Replaced the promotional dark sidebar with quiet persistent navigation, permission context, and a native mobile dialog with focus containment and Escape support.
- Added hash-based page/case navigation, so refresh and browser history retain the selected screen and incident.
- Replaced floating KPI cards with an inline workload summary, an open-case queue and supporting audit evidence. The trend explicitly covers seven UTC calendar dates, including dates with zero reports.
- Made the full queue denser, with case ID/title, category, severity, status, assigned analyst and updated time. Server search, filters, sorting, pagination and recovery remain connected to the API. Mobile records expose labeled fields.
- Reworked investigation surfaces and property controls; failed summary saves preserve the draft and errors. Missing cases have retry recovery. Late account-creation completions cannot show success notices on an unrelated route. Mutations retain audit-backed API behavior.
- Gave login analysis a visible deterministic rule, explicit CSV requirements and evidence-led results. Replacing input clears stale results; unreadable and invalid files produce actionable errors.
- Added a compact member directory, explicit permission descriptions and an admin account form. The current API supports provisioning and read-only existing roles; the UI does not imply role editing.
- Replaced the authentication hero with a focused sign-in form and real error feedback.

## Architecture

The React/FastAPI/SQLAlchemy stack and API contracts are unchanged. `workspace.tsx` owns overview and member screens; `App.tsx` owns session/shell/navigation. Existing form, incident and analyzer boundaries remain. `tokens.css` centralizes semantic roles; `style.css` contains shared and screen styles; `responsive.css` owns viewport adaptations and reduced motion. Inter is bundled through `@fontsource-variable/inter`, with no runtime font CDN. The original backend source and migrations were not changed.

## Screenshots

All captures use real Chromium and an isolated synthetic demo database. Before and after counts can differ because the browser walkthrough creates synthetic cases and users. Each set includes desktop 1440×900, laptop 1280×800 and mobile 390×844 at 2×. The full image files are retained, not retouched.

| Screen | Before desktop | After desktop | After mobile |
|---|---|---|---|
| Overview | [Before](screenshots/before/dashboard-desktop.png) | [After](screenshots/after/dashboard-desktop.png) | [Mobile](screenshots/after/dashboard-mobile.png) |
| Queue | [Before](screenshots/before/incidents-desktop.png) | [After](screenshots/after/incidents-desktop.png) | [Mobile](screenshots/after/incidents-mobile.png) |
| Investigation | [Before](screenshots/before/detail-desktop.png) | [After](screenshots/after/incident-1-desktop.png) | [Mobile](screenshots/after/incident-1-mobile.png) |
| Analyzer | [Before](screenshots/before/analyzer-desktop.png) | [After](screenshots/after/analyzer-desktop.png) | [Mobile](screenshots/after/analyzer-mobile.png) |
| Team | [Before](screenshots/before/team-desktop.png) | [After](screenshots/after/team-desktop.png) | [Mobile](screenshots/after/team-mobile.png) |
| Login | [Before](screenshots/before/login-desktop.png) | [After](screenshots/after/login-desktop.png) | [Mobile](screenshots/after/login-mobile.png) |

[Activity](screenshots/after/activity-desktop.png), [reporting](screenshots/after/new-desktop.png), [mobile navigation](screenshots/after/navigation-mobile.png), [failed draft recovery](screenshots/states/summary-error-preserves-draft.png), [analyzer evidence](screenshots/states/analyzer-results.png), [empty queue](screenshots/states/queue-empty.png), [service error](screenshots/states/queue-error.png), [loading](screenshots/states/queue-loading.png), [keyboard focus](screenshots/states/queue-keyboard-focus.png).

## Verification

| Check | Actual result |
|---|---|
| `npm ci` | Passed against final lockfile; 247 packages audited, zero reported vulnerabilities at execution time |
| `npm run typecheck` | Passed |
| `npm run lint` | Passed |
| `npm test` | 8 passed |
| `npm run build` | Passed |
| `python -m pytest -q` | 23 passed; one existing Starlette/httpx deprecation warning |
| `python -m ruff check .` | Passed |
| Real browser walkthrough | Passed: login/logout, creation, edit/error draft, status, severity, assignment, notes, resolve/reopen, persisted case URL, search/filter/clear, empty/error/retry, CSV validation/import/analysis/conversion, admin/analyst/viewer, mobile dialog/Escape, reduced motion, no JS page errors |
| Viewports | Screens captured at all three required sizes; no page-level horizontal overflow |
| StyleSeed | Legacy resolve/check succeeded; reviewer-applied ss-score rubric 87/100. Registry scanner blocked SS000. [Full review](STYLESEED_REVIEW.md) |

A clean install initially encountered an esbuild file lock while Vite was running. Stopping the verification server and rerunning `npm ci` resolved it; subsequent checks passed. A browser test initially exposed a missing exact role label in the account form; it was corrected and the full walkthrough passed.

## Exact local startup

In PowerShell with Python 3.11+ and Node.js 22.12+ / npm installed:

```powershell
Set-Location 'C:\Users\tyler\OneDrive\Desktop\IncidentOps'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\scripts\dev.ps1 -Demo
```

Open http://localhost:5173. The explicit demo account is documented in README. The launcher runs migrations, installs the frontend, starts the API on 8000 and Vite on 5173. Ctrl+C stops the services. Stop a running development server before rerunning a clean dependency install on Windows.

Manual API terminal:

```powershell
Set-Location 'C:\Users\tyler\OneDrive\Desktop\IncidentOps'
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m incidentops.manage demo
.\.venv\Scripts\python.exe -m uvicorn incidentops.main:app --host 127.0.0.1 --port 8000
```

Manual frontend terminal:

```powershell
Set-Location 'C:\Users\tyler\OneDrive\Desktop\IncidentOps\frontend'
npm ci
npm run dev
```

After starting an explicit demo workspace, browser verification is reproducible with `python tests/browser_smoke.py`. Screenshots/probes use `python scripts/capture_screens.py` and require the locally installed StyleSeed skill. Both use `INCIDENTOPS_URL` when a different local URL is necessary. Tests create synthetic users and cases; use a disposable demo database.

## Remaining limits

StyleSeed's registry-only deterministic scanner cannot certify this legacy-lock project; the 87/100 score is an agent-applied rubric, not an automated numeric score or owner approval. Appearance probes cover selected opaque color pairs and Latin Inter, not a full accessibility audit. Chromium was exercised; Firefox, Safari, screen-reader testing, Docker/PostgreSQL and public deployment were not run. Existing API role changes are not supported. Queue filters are local to the mounted queue; a case/page URL persists, but filter state does not survive leaving the screen. No merge or public deployment was performed.

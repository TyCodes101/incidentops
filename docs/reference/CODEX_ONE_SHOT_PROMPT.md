# CODEX MASTER PROMPT — INCIDENTOPS FULL-STACK PORTFOLIO APPLICATION

You are my autonomous senior full-stack engineer, security-minded backend developer, QA engineer, and UI designer. Work IN THIS REPOSITORY. Do not just give me ideas, an outline, pseudocode, or instructions for later: inspect the existing code, then IMPLEMENT, RUN, TEST, DEBUG, and DOCUMENT the finished application in this workspace. Aim to complete this in one uninterrupted coding run. Be proactive and make reasonable decisions without pausing for minor preferences. Never claim a test, deployment, screenshot, or feature succeeded unless it actually did.

## Project and goal

Project name: **IncidentOps — Security Incident Command Center**.

This is a DEFENSIVE cybersecurity case-management application, not an attack tool, live intrusion-detection system, or security-monitoring agent. A legitimate security/IT team can record a suspected compromise, triage it, assign an analyst, track actions and evidence notes, change severity/status, read an audit timeline, and see dashboard metrics. An optional demonstration log-import module should flag suspicious patterns in *synthetic or user-provided authorized sample login logs* and create a draft incident. Make clear that rule-based flags are informational, not proof of compromise.

Primary audience: recruiters hiring entry-level software engineers, security engineers, and IT analysts. The end result must demonstrate **Python, FastAPI, React, TypeScript, SQL/PostgreSQL, REST API design, role-based authorization, automated tests, Docker, GitHub Actions, and deployable architecture**. The app must be actually functional end-to-end and polished enough for a portfolio demonstration, not a static mockup.

## What already exists — preserve and improve it

This repository starts as a Python FastAPI backend. Read `README.md`, `PROJECT_ROADMAP.md`, `incidentops/main.py`, `db.py`, `models.py`, `schemas.py`, `tests/`, `pyproject.toml`, `Dockerfile`, `compose.yaml`, `.env.example`, and `.github/workflows/ci.yml` BEFORE changing architecture. Existing endpoints include `/health`, `/incidents`, `/incidents/{id}`, `/incidents/{id}/history`, and `/metrics`. There are SQLAlchemy incident and incident-event tables, simple severity/status values, a shared `X-API-Key` check, pytest tests, SQLite fallback, PostgreSQL Compose, and backend CI. **Keep working functionality and migrate it thoughtfully.** Preserve or adapt tests as authentication evolves. Do not simply delete the tests to make the build green.

## Non-negotiable success criteria (implement these first, in this order)

### 1. Working full-stack product

- Create a `/frontend` Vite + React + TypeScript application (use stable, widely supported dependencies) and connect it to the FastAPI backend. Use a readable component structure, typed API client, and clear separation of UI and server logic.
- Provide a gorgeous, cohesive, professional visual design: predominantly white/near-white surfaces with dark navy/charcoal text, tasteful electric-blue accent, accessible contrast, refined typography, restrained rounded corners/shadows, responsive desktop/mobile layout, and good whitespace. Avoid generic unfinished template vibes. Make it look like a modern, believable SaaS SOC incident command center.
- Working screens/views: **Dashboard**, **Incidents**, **Incident Detail**, **New Incident**, and **Activity/Audit Log**. Optional simple **Settings/About** page. Sidebar/header nav must work.
- Dashboard cards: total, open, investigating, resolved, high/critical. Include a real chart from API data (severity distribution and incident trends over time), recent incidents, and recent activity. Use a chart library if reasonable; don't invent data in dashboard charts without labeling it demo data.
- Incident list: server-backed search, filters for status/severity/category, sort, pagination, and click-through. Color-coded severity/status pills. Loading, empty, offline/error, and successful operation states.
- Create/edit: validated incident title, description, category, severity; assign owner when accounts exist; update status; add investigation notes; close/resume incident; record all changes in the audit trail. Use an accessible modal or dedicated form and display useful server-side validation errors.
- Incident details: descriptive header, owner, timestamps, status/severity, notes, and chronological, read-only history including actor and action. Every button must work; no dead controls or fake counts.

### 2. Defensible authentication and authorization

- **Replace the demo shared API-key model for browser use** with real user accounts and secure authentication. Use a maintainable solution: password hashes via Argon2/bcrypt, server-side sessions or signed, short-lived tokens in `HttpOnly`, `SameSite` cookies with Secure in production; don't store auth credentials in localStorage. Handle CSRF if cookie-authenticated state-changing requests and cross-site conditions permit it. Add session expiry/logout, no plaintext passwords.
- RBAC with **Admin**, **Analyst**, and **Viewer**. Viewers can read; Analysts can create/update incidents/notes; Admins can additionally manage users and assignments. Enforce authorization on the backend for every endpoint and test forbidden operations. Avoid broken object-level authorization and don't trust browser-supplied role/owner claims.
- Add a nice login page. For local demo ONLY, provide an explicitly opt-in seeded demo user and realistic synthetic incidents; document demo credentials in README but not in production configuration. Never hardcode production secrets or turn on demo seeding in production. Add a bootstrap/admin creation command or documented environment variables for real setup.
- Configure CORS/origin restrictions, body limits/validation, secure error messages, dependency handling, basic login throttling (or documented equivalent), and safe logging (never log credentials/tokens). Keep secrets in env and `.env` ignored. Explain that this is a portfolio project, not an audited commercial SOC.

### 3. Backend, database, correctness

- Keep FastAPI/SQLAlchemy/Pydantic. Add tables for users, incident notes, assignments, and immutable audit events as needed; maintain foreign keys and timestamps and use UTC consistently. Introduce **Alembic migrations** so schema updates are reproducible; avoid relying only on `Base.metadata.create_all()` in production.
- Expand REST API with appropriately secured endpoints for `/auth/*`, incidents CRUD/update/assign/notes/history, stats/trends, activity, and users (admin only). Keep OpenAPI docs helpful; align endpoint and frontend data types. Consistent validation, HTTP status codes, pagination metadata, and API error handling.
- Provide search, filtering, sortable results, recent history, and statistics computed from persisted data rather than fake frontend arrays. Audit should capture creation, severity/status change, assignment, note addition, and actor.
- PostgreSQL in Docker Compose and a straightforward SQLite-based dev/test mode if helpful. Make rerunning/refreshing the project reliable without resetting real data. Seed only synthetic demo incidents.

### 4. Automated testing and CI

- Backend: strong pytest coverage for health, authentication, password/session handling, 401/403, roles, creation, editing, validation, sorting/filtering/pagination, assignment, audit, notes, metrics, and migration/smoke behavior.
- Frontend: Vitest + React Testing Library (or equivalent) for core interactive states: login errors, filtering, creating an incident, updating status, error/loading states; avoid tests that only snapshot static HTML.
- Include formatting/lint/type checks (Ruff for Python; ESLint + `tsc --noEmit` for frontend), a frontend production build, and GitHub Actions CI running backend tests, frontend checks/tests/build, and preferably Docker image build. The workflow must reference files that exist and have correct working directories.
- If possible report honest coverage, but DO NOT make up a number. Do not weaken assertions or skip meaningful tests to obtain passing status. Fix failures.

### 5. Reliable local run and containerization

- Provide a single easiest development command or documented 2-terminal setup; provide `docker compose up --build` or equally simple workflow bringing up **frontend + backend + PostgreSQL** with functional networking and health checks. Use appropriate service ports and reverse proxy to keep login secure under one origin if feasible.
- `.env.example` must list all required variables with safe development placeholders and unambiguous instructions; never commit `.env`. Keep DB private to Docker network. Avoid bundling secrets into client JS. Add `Makefile` or cross-platform npm/PowerShell-friendly scripts, with Windows-friendly instructions.
- Verify Compose syntax/build/start if Docker is available. If Docker or internet are unavailable, explicitly report what was blocked rather than pretending successful verification.

### 6. Portfolio-ready documentation

- Rewrite README with overview, actual features, tech stack, short architecture explanation, screenshots if screenshot tooling is available, repository tree, local setup for Windows PowerShell and macOS/Linux, Docker setup, seeded demo access (dev only), test commands, API docs, environment variables, troubleshooting, and deploy instructions for a realistic provider (such as Render/Railway/Fly plus managed PostgreSQL). No fake live URLs.
- Add Mermaid architecture/data-flow diagram and `docs/` containing example API flows, a security/design-decisions note, and demo walkthrough of a believable phishing or suspicious-login case. Include a crisp GitHub repo description and optional resume bullets **labeled for use only after features are verified**.
- Deployment: if I have not supplied cloud credentials, do NOT ask for secrets just to finish coding. Prepare deploy config and step-by-step deployment documentation; do not claim it is live. Never commit tokens or use paid resources without approval.

## Differentiator — add after the above is functioning

Add a safe, demo-only **Login Event Analyzer** for authorized synthetic/test log data. No packet sniffing, credential harvesting, scanning, or active exploitation. Support simple CSV import with columns like timestamp, username, source_ip, success (or a documented schema), enforce size/type limits, and use transparent configurable rules: e.g., 5+ failures for the same account in 10 minutes, or repeated failures followed by success. Show flagged patterns with the count/rule/time window and allow an analyst to turn a flagged event into an incident. Avoid labeling mere flags as confirmed malicious activity. Include import validation, tests, and 10–30 rows of clearly synthetic demo data. If this feature threatens core application completion, finish the core app and document the analyzer as an honest future milestone.

## Design specifics

- Product name **IncidentOps**; tagline **Security incidents, under control.**
- Premium professional look suitable for recruiter demos; distinctive dashboard visual hierarchy. Modern responsive sidebar, top search bar, profile menu, subtle chart transitions, small alert indicators, tasteful iconography, accessible navigation and keyboard use.
- Use realistic fake content ONLY, clearly marked Demo. Example categories: Phishing, Identity & Access, Malware Report, Data Exposure, Suspicious Login, Endpoint, Other.
- Avoid real personally identifiable data, real user secrets, unauthorized logs, or real third-party integrations. No unnecessary paid services or large dependency overhead.
- Distinctive thoughtful empty states and inline toasts; form field validation; no lorem ipsum; no broken links, placeholder buttons, or charts with unexplained hard-coded numbers.

## Work process — important

1. Inspect repo and run existing backend tests first. Summarize only briefly in your internal work; then start implementing. Follow existing design where it makes sense.
2. Create a short implementation checklist in `docs/IMPLEMENTATION_CHECKLIST.md` and keep it current while working. Do NOT stop after planning.
3. Implement in sensible milestones: database/auth/API, frontend integration and UI, testing, Docker/CI, docs, optional analyzer.
4. At each milestone run relevant commands, inspect errors, and fix. Search project code before changing function signatures. Avoid unnecessary rewrites. Don't discard starter functionality or erase Git history.
5. Install allowed open-source dependencies as needed; prefer maintained libraries and lockfiles. Avoid huge unreviewed dependency sprawl.
6. Stay within the current workspace. Do not push to a remote repository, create cloud resources, spend money, or submit user data without explicit permission. You MAY prepare commands/configs for me to perform those steps.
7. If blocked by credentials, unavailable tools, services, or dependency installation: complete all feasible local work, document the specific blocker and commands I can run, and continue. Ask me a question only if absolutely impossible to proceed safely; otherwise decide and implement.
8. Keep secrets out of source, logs, screenshots, and Git. Treat any supplied sample incident/log data as demo-only.
9. Check cross-platform quick-start steps. Prefer a reliable, completed app over an inflated feature list. No pretending features or tests work.

## Final acceptance test — actually perform it if environment permits

- Backend tests and lint pass.
- Frontend typecheck/lint/tests/build pass.
- Local or containerized stack starts cleanly.
- Demo user can sign in, create a sample incident, search/filter it, change severity/status/assignment, add a note, see accurate updated metrics and audit history, and sign out.
- Viewer cannot perform Analyst/Admin actions; invalid inputs rejected; unauthenticated API cannot expose incident data.
- README matches actual commands, project compiles without manual copy-pasted code, GitHub Actions references the correct commands.
- No broken navigation, fake buttons, demo secrets in production build, or fabricated results.

## Final response format

Once finished, respond with:
1. **What you implemented** (group by frontend/backend/security/testing/DevOps).
2. **What commands you actually ran and exact results** (including tests counts if known).
3. **How I can launch it on Windows in 3–5 commands**.
4. **Demo login** and how demo-only seeding is turned off for production.
5. **Remaining limitations / anything unverified**.
6. **Next steps to push to GitHub and deploy** (without actually pushing/deploying without permission).
7. **Three accurate resume bullets** based ONLY on implemented and verified features, with placeholders instead of fictional metrics.

Start now. Inspect, implement, and verify. Do not stop at a plan. The objective is a functioning recruiter-ready portfolio app in this one Codex run.

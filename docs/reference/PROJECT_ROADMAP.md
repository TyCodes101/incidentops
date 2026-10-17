# IncidentOps — 5-milestone portfolio plan

## Goal
Create a polished incident response dashboard with a testable API, PostgreSQL database, GitHub Actions, Docker, and a live demo. Aim for a distinctive portfolio project for entry-level software engineering, cybersecurity engineering, and IT systems roles.

### Milestone 1 — Verify the starter (about 1–2 hours)
- [ ] Create a new GitHub repository named `incidentops`.
- [ ] Set up the virtual environment and run `pytest -q`.
- [ ] Start the API and test POST/GET/PATCH in Swagger.
- [ ] Read through the database schema and tests to understand the code.
- [ ] Write a short README note explaining how incidents and audit events are related.

### Milestone 2 — Docker + PostgreSQL (about 2–3 hours)
- [ ] Configure unique secrets in `.env`.
- [ ] Run `docker compose up --build`.
- [ ] Confirm the incidents persist when the API restarts.
- [ ] Capture screenshots of the API and Docker containers.

### Milestone 3 — React dashboard (about 4–6 hours)
- [ ] Create `/frontend` with Vite + React + TypeScript.
- [ ] Add summary cards for open/resolved incidents and severity breakdown.
- [ ] Add incident creation form, table filters, and status changes.
- [ ] Use a secure server-side gateway for the API key; do not ship it to the browser.
- [ ] Write UI tests for incident state changes.

### Milestone 4 — Security + database quality (about 4–6 hours)
- [ ] Implement accounts and RBAC; do not rely on a shared demo API key.
- [ ] Add Alembic migrations, structured audit events, and logs.
- [ ] Test 401/403 responses and malicious/invalid inputs.

### Milestone 5 — Deploy + prove reliability (about 3–5 hours)
- [ ] Deploy API/container and a managed PostgreSQL database with secrets.
- [ ] Configure CI to pass and demonstrate a healthy production endpoint.
- [ ] Write a short architecture diagram, screenshots, and demo walkthrough.
- [ ] Report measured test count, coverage, and endpoint latency, if verified.

## Resume entry — only after you complete the milestones

**IncidentOps | Security Incident Management Dashboard** | Python, FastAPI, PostgreSQL, React, Docker, GitHub Actions
- Developed a RESTful security-incident tracking application with priority workflows, PostgreSQL persistence, and a filterable React dashboard.
- Implemented authenticated APIs, audit logging, integration tests, containerized services, and CI checks through GitHub Actions.
- Deployed to [verified hosting provider]; recorded [measured test count/coverage and benchmark results].

Replace bracketed placeholders only with facts you can substantiate. Don't claim completed features before you finish them.

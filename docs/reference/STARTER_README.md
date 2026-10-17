# IncidentOps — Security Incident Triage API

**Status: starter project.** A realistic backend portfolio project designed to build skills not yet demonstrated by a nutrition-tracking app: security workflows, REST API design, PostgreSQL, Python testing, containerization, and CI.

## Features already implemented

- FastAPI REST endpoints to create, view, filter, and update incidents
- SQLAlchemy database models and a two-table relational schema
- Severity levels, incident statuses, pagination, and validation
- API-key protection for incident data (development/demo use only)
- Audit trail recording creation and status transitions
- Aggregated metrics grouped by severity and status
- SQLite for local development; PostgreSQL configured through Docker Compose
- Pytest API integration tests and GitHub Actions CI workflow
- Swagger API documentation at `/docs`

## Quick start (local)

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
export INCIDENTOPS_API_KEY='change-this-local-demo-key'  # PowerShell: $env:INCIDENTOPS_API_KEY='change-this-local-demo-key'
uvicorn incidentops.main:app --reload
```

Then visit `http://127.0.0.1:8000/docs`. Expand a protected endpoint, click **Try it out**, and supply the `X-API-Key` header. The starter uses a simple shared key for demonstration, not user accounts.

Try it with curl:

```bash
curl -X POST http://127.0.0.1:8000/incidents \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: change-this-local-demo-key' \
  -d '{"title":"Suspicious sign-in activity","description":"Five failed attempts","severity":"high","category":"identity"}'
curl -H 'X-API-Key: change-this-local-demo-key' http://127.0.0.1:8000/metrics
```

## Run with Docker and PostgreSQL

1. Install Docker Desktop.
2. Copy `.env.example` to `.env` and replace **both** values with long unique secrets.
3. Run `docker compose up --build`.
4. Open `http://127.0.0.1:8000/docs`.

Docker binds the API to localhost, and the database is not exposed to the host. Do not check your `.env` file or any tokens into Git.

## Test and lint

```bash
pytest -q
ruff check .
```

The GitHub Actions workflow automatically runs these on pushes and pull requests.

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Public health check |
| POST | `/incidents` | Create an incident |
| GET | `/incidents` | Filter and paginate incidents |
| GET | `/incidents/{id}` | Get one incident |
| PATCH | `/incidents/{id}` | Change incident status |
| GET | `/incidents/{id}/history` | Get immutable status-event history |
| GET | `/metrics` | Summary counts for an operations dashboard |

Only the health endpoint is public. All incident and metric routes need an `X-API-Key` request header.

## Next milestones to make it stand out

1. **Dashboard:** build a React/TypeScript UI showing incident counts, severity, trends, and a filterable table.
2. **Real auth:** replace the shared API key with user accounts, role-based access control (RBAC), and permissions tests.
3. **Schema migrations:** adopt Alembic rather than relying on `create_all` at application startup.
4. **Cloud deployment:** deploy the container and managed database to a platform of your choice; configure environment secrets, health checks, and logging.
5. **Quality evidence:** document test pass rate, API latency, incidents processed, and deployment status with truthful reproducible numbers.
6. **Security hardening:** add input rate limiting, audit actor IDs, structured logs, and secure secret rotation.

## Why this complements your resume

This project demonstrates Python backend development, relational database design, an authenticated REST API, audit events, tests, Docker, and CI/CD. It is deliberately different from MacroMesh/Calorie Compass, Ruby on Rails Poker, and your Red-Black Tree project.

**Do not add it to the resume as a completed project yet.** Build/run the starter, push it to your GitHub account, add the UI/auth milestones, and deploy it. Then write resume bullets using only the features and verified metrics you implemented.

> Educational demo only. Do not store real credentials, private security incidents, or sensitive information in this starter. API-key-only authorization is not production-grade.

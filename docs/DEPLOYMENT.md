# Free public demonstration deployment

Reviewed 2026-10-17. Deployment success is recorded separately in the release report; these instructions alone are not proof of a running service.

## Hosting choice

| Option | Compatibility and persistence | Free-plan limitations | Decision |
|---|---|---|---|
| Vercel Hobby + Neon Free | React static assets, native FastAPI Python function, managed PostgreSQL, one HTTPS origin | Personal/noncommercial Hobby use, finite function/traffic quotas; Neon currently 100 CU-hours and 1 GB per project; cold starts and suspension at limits | Preferred: existing authenticated Hobby/Free accounts, no billing enabled |
| Render Free web service + Neon Free | Existing Docker image and persistent external PostgreSQL | Free web services sleep; 750 shared monthly instance-hours; separate accounts/ingress setup | Viable alternative, more setup |
| Render Free web + Render Free PostgreSQL | Native full stack | Free database expires after 30 days | Unsuitable for a durable portfolio database |

Sources: [Vercel FastAPI](https://vercel.com/docs/frameworks/backend/fastapi), [Hobby](https://vercel.com/docs/plans/hobby), [Neon pricing](https://neon.com/pricing), [Render Free](https://render.com/docs/free). Free limits can change. Do not upgrade or attach payment methods automatically.

## Security and release sequence

1. Require final CI, runtime dependency audits and complete container scan reports to pass. Do not deploy with an unresolved critical finding.
2. Create a dedicated Neon Free database, with no operational or personal data. Preserve any existing unrelated databases. Prefer a pooled TLS URL for the function and a direct TLS URL for migrations. Keep the existing SQLAlchemy/psycopg driver: `postgresql+psycopg://...?...sslmode=require`.
3. Privately run `python -m alembic upgrade head` once against that database. Do not run migrations on every function request.
4. Set `PUBLIC_DEMO=1` and privately run `python -m incidentops.manage public-demo`. This explicit seed requires an empty dedicated database and creates 12 fictional cases, `demo.analyst`, and `demo.viewer`. It creates no administrator. Existing operational deployments must use private `admin` provisioning instead.
5. Configure server-only `DATABASE_URL`, `APP_ENV=production`, `APP_ORIGIN=https://<canonical-host>`, `PUBLIC_DEMO=1`. Set build-time `VITE_PUBLIC_DEMO=1` only for the public sandbox. The latter contains no secret; it reveals the intentionally public sandbox account names/password and data-use notice.
6. Import the repository into the existing Vercel Hobby team. Use `vercel.json` and `server.py`. The build installs/builds the React client. The adapter explicitly declares `frontend/dist` as a static mount for the platform builder to discover/package, after mounting the original API at `/api`; cookies, permissions and CSRF remain server enforced. Assets are eligible for CDN delivery and retained in the function bundle as a fallback. Store database credentials as sensitive environment variables, never in Git or browser JavaScript.
7. Verify actual HTTPS, health, authentication/logout, CSRF/origin rejection, roles, mutations, notes/audit, persistence, CSV and mobile layout. Only then advertise a live URL.

Production login quotas are shared through PostgreSQL; demo writer quotas are 200/day globally and 30/hour/account. They are abuse bounds, not a DDoS guarantee. Public visitors share the fictional workspace. The owner must monitor free quotas, retain provider backups/exports and decide when to archive synthetic records; no silent destructive reset is implemented. Free resources provide no uptime SLA. Preview hosts are not allowed write origins unless deliberately configured for an isolated preview database.

The Vercel-managed Neon organization rejects direct project creation through the Neon API. Use its existing Vercel Storage integration and explicitly select Free. Do not reuse another project's database or create a paid organization as a workaround.

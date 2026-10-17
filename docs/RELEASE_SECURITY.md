# Release security review

This review covers the single-workspace IncidentOps API, React client, database migrations, Docker images, CI and deployment boundaries. It is not a commercial penetration test or security certification.

## Confirmed issues corrected

| Finding | Correction | Evidence |
|---|---|---|
| The API buffered an entire write before checking its size | An outer ASGI middleware rejects declared or streamed bodies above 64 KiB, before buffering excess bytes or invoking model parsing. The JSON 413 contract is retained. | Chunked, declared-length and exact-limit regression tests |
| Timestamp arithmetic could overflow for valid minimum ISO dates in CSV | Compare elapsed timedeltas rather than subtracting ten minutes from the minimum datetime. The documented deterministic rule is unchanged. | Minimum-date regression plus existing CSV tests |
| Known development demo credentials could authenticate if a development database reached production | Production rejects the development demo username; the existing production seed refusal remains. | Production demo-login rejection test |
| Incorrect production environment values could silently select development defaults | Startup validates the environment mode, exact HTTPS origin and explicit PostgreSQL configuration. | Production configuration regression tests |
| A PostgreSQL session timezone could extend or shorten session expiry | Preserve aware timestamp offsets; attach UTC only for naive SQLite timestamps. | Existing expiry test plus PostgreSQL timezone regression in CI |
| Parallel hashing and rate-limit bookkeeping had resource/concurrency gaps | Password verification has a two-slot concurrency bound; the per-process login cache is locked and bounded to 10,000 client keys. | Concurrency and cache-bound tests; existing ten-attempt throttle test |
| Expired sessions accumulated indefinitely | Successful session creation removes expired session records. | Expired-session cleanup regression |
| Concurrent identical account creation could become an unhandled database exception | Roll back uniqueness conflicts and return the existing 409 response. | Database-conflict recovery regression |
| Local test cookies, environment files and tooling could enter Docker build contexts | Exclude local runtime, environment, skill, scratch and database files. | Docker ignore review; tracked history/path scan |
| Mobile navigation dialog lacked an accessible name; its brand link left the drawer open | Named the dialog and close it on brand navigation. Login now has a top-level heading. | Source review and final viewport/browser captures |

The API keeps Argon2 password hashing, opaque server-side sessions with hashed tokens, eight-hour expiration, logout revocation, HttpOnly/Secure/SameSite cookies, authenticated-write CSRF checks, exact-origin checks and role enforcement. No public signup or user-role editing was added. Incident mutations and audit events still commit together.

The Compose API has no host port. Its private reverse proxy overwrites incoming forwarded-client headers before forwarding them, so Uvicorn can use client IPs for the existing login throttle. Trust-all proxy handling is confined to this unpublished private Compose service; do not expose that API directly or copy this trust setting to a public service without reviewing its ingress.

## Dependency and data checks

The committed frontend lockfile audit found no vulnerabilities at the time of this release review. pip-audit checked pinned locally installed Python runtime dependencies; the CI job additionally audits the packages actually present in the built API image. Container reports cover the actual API, Nginx and PostgreSQL images, using a digest-pinned Trivy release, without giving the scanner the Docker socket or checkout credentials. Critical findings block the release; high findings remain visible for review. A missing/unsupported report cannot pass the gate.

The scoped Git history scan checks token/private-key signatures and sensitive paths without printing candidate values. It found no matching candidates in the scanned history. Public synthetic development/CI passwords are intentional test fixtures, not operational credentials. This scan does not prove the absence of every possible secret.

## Public demonstration boundary and remaining risks

- Use a dedicated database containing only fictional incidents. Do not connect a public demo to personal, operational or other applications' records.
- Never publish administrator credentials. A public demonstration account should have the minimum role required; keep owner provisioning private.
- Login throttling remains process-local. Run a single API process/instance or add a shared/edge limiter before scaling or moving to an ephemeral serverless runtime. The local bound is not a distributed rate-limit guarantee.
- Shared demo writes can be abused or fill storage; a writable public demo needs explicit quotas/reset and ownership rules. Do not grant public account-provisioning rights.
- No MFA/SSO, password recovery, account deactivation UI or tenant isolation. This limits suitability for sensitive production use.
- Audit records cannot be edited through the API, but database administrators can change them; there is no external tamper-evident audit store.
- Backups/restoration are verified with a disposable database. That does not configure a production backup schedule, retention, point-in-time recovery or recovery objective.
- Require provider HTTPS, Secure cookies, exact origin configuration, managed secrets and encrypted database transport on public networks. Validate the actual hosted endpoint before advertising it.
- Package/container audits are dated observations, not a guarantee against future or undisclosed vulnerabilities. High/unfixed findings must be recorded with their practical impact.

## References

[OWASP session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), [OWASP CSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html), [Starlette middleware](https://www.starlette.io/middleware/), [PostgreSQL backup](https://www.postgresql.org/docs/16/app-pgdump.html), [Trivy container scanning](https://trivy.dev/docs/latest/target/container_image/).

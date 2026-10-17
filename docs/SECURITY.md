# Security and design decisions

This is a single-workspace portfolio application. All authenticated roles can read all cases and the member directory. Directory data excludes password hashes; only admins may create users or change assignments. Analysts and admins can create/update cases and notes. Viewers cannot mutate. There is no public signup, case deletion, history editing, or user deletion.

Passwords use Argon2 library defaults and a dummy hash check for nonexistent users. Sessions use random 256-bit tokens; only SHA-256 token digests persist. Sessions expire after eight hours and logout removes the session. The cookie is HttpOnly and SameSite Strict; production enables Secure. A separate readable random CSRF cookie must match a custom header on authenticated writes. Exact origin validation also covers login. No wildcard CORS, browser localStorage tokens, or frontend secrets.

The API rejects declared or streamed write-body data above 64 KiB before buffering excess bytes; the container proxy also rejects oversized bodies at ingress. Pydantic bounds fields and rejects unexpected case mutation keys. SQLAlchemy parameterizes database queries. Login throttling is ten attempts per client IP per minute in one process, with locked bookkeeping and a bounded client-key cache; password verification concurrency is bounded. Multiple instances or ephemeral serverless runtimes need shared/edge enforcement. Do not trust arbitrary forwarded headers without explicitly trusted proxies.

Cases, assignments, sessions, events and notes use relational keys. Audit and case changes commit together. No-op updates do not create new events. API audit records cannot be edited or deleted; a database operator could still modify them. Use independent restricted runtime DB roles, backups and external append-only logging for stronger guarantees. Actor usernames are stored as strings; usernames cannot be changed through this app.

Migrations are explicit. Production does not use create_all. Tests use isolated in-memory schemas; a separate migration test checks upgrade, repeated upgrade, downgrade/re-upgrade and preservation of a starter incident. SQLite foreign keys are enabled through the app engine; Postgres is the primary container database.

The CSV analyzer reads bounded example input in memory and does not retain raw CSV. It flags five failures within ten minutes for the same username across source IPs, with a success-after-failures indicator. It is a demonstration rule; behavior, clock errors and shared IPs can cause false positives. Convert a flag to a case for investigation, not as a verdict. Fixtures use reserved addresses and fictional accounts.

Production gaps: no MFA/SSO, password recovery or deactivation UI; no shared rate limiter; expired sessions are cleaned on successful login; no tenant isolation; no field-level database encryption; no optimistic locking on case edits; no commercial security audit. Require HTTPS and operational hardening before storing sensitive records.


The release adds fail-closed production environment/origin/database checks, refuses the development demo account in production, preserves PostgreSQL timezone-aware session expiry, handles concurrent username conflicts, and excludes verification credentials from image build contexts. See [release security findings and remaining risks](RELEASE_SECURITY.md).

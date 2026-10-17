# IncidentOps — Agent Operating Rules

IncidentOps is a working security incident management application. Preserve its behavior; redesign the visual and interaction system around analysts' actual workflow.

## Engineering boundaries
- Existing stack: React 19, TypeScript, Vite; Python FastAPI, SQLAlchemy, Alembic. Do not rewrite the stack solely for appearance.
- Preserve secure server-side sessions, HttpOnly cookies, CSRF/origin checks, Admin/Analyst/Viewer permissions, incident creation/editing, assignments, notes, resolution/reopening, history, audit activity and CSV analyzer.
- Never replace API-backed data with static mocks. Synthetic demonstration data must be clearly marked as such.
- Do not introduce dependencies, run third-party installers, deploy paid services, push directly to main, or auto-merge without permission.

## Durable StyleSeed method
1. Before touching UI, read STYLESEED.md and docs/CODEX_STYLESEED_REDESIGN.md. These are IncidentOps-specific instructions and the initial approved design direction.
2. Locked grammar: `operations-console`; adapter: `product-ui`; recipe: `enterprise-workbench`; palette: `cobalt-instrument`, overridden by our muted slate-blue brand action. Use this functional system, not a marketing-landing-page or consumer-dashboard grammar.
3. When StyleSeed is installed, run `$styleseed resolve` and read the generated effective rules and manifest. Next use `$styleseed build`, `$styleseed score` and `$styleseed verify` as the installed workflow supports. Current Codex entry point is `$styleseed`; older `$ss-*` labels are internal workflows.
4. If StyleSeed is not installed or a workflow is unavailable, disclose the limitation. Do not fabricate scores, screenshots or StyleSeed execution. Do not auto-install third-party tools without explicit permission.
5. Only revise STYLESEED.md after the owner approves a changed visual decision. Do not invoke optional learning/export/promotions automatically.
6. A StyleSeed score >=80 is a target for the code gate, not proof of expert design or owner approval. Rendered visual inspection and functional verification are separate requirements.

## Visual contract
- Light, disciplined, operations-focused workspace: charcoal typography, white/off-white canvas, quiet cool gray surfaces, muted slate-blue actions, meaningful status colors.
- Case queue and investigations are primary; metric panels and charts exist only when they support an analyst's decision.
- Real data, clear information architecture, accessible controls, stable table columns, consistent spacings, tabular figures and monospaced evidence only when appropriate.
- No generic AI dashboard conventions: repeated icon-in-circle cards, gradient blobs, glass panels, identical four-up marketing widgets, huge empty hero banners, irrelevant promotional sidebar text, neon/security terminal cosplay, or excessive pill buttons.
- Use shared semantic CSS tokens and reusable components. Prefer 4-8px radii, hairline dividers and minimal surface elevation.
- Support desktop 1440×900, laptop 1280×800, mobile 390×844. Reduced-motion preferences, visible focus, keyboard controls, useful loading/error/empty states are required.

## Verification
For frontend changes: `npm ci`, `npm run typecheck`, `npm run lint`, `npm test`, `npm run build` in `frontend/`. For API regression: `python -m pytest -q`, `python -m ruff check .` at repo root. Run browser walkthroughs for login, queue, incident details, notes, assignments, analyzer and all roles. Visually inspect actual screenshots at required viewports. Document passed, failed and skipped tests individually. Work on a branch and submit a PR with before/after screenshots; do not auto-merge.

StyleSeed is independent third-party open-source software: https://github.com/bitjaru/styleseed

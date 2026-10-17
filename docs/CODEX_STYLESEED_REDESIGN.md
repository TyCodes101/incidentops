# IncidentOps — full StyleSeed enterprise workbench redesign

## Product goal
Build a bespoke, credible security operations workbench for managing reported incidents. The current application already functions. Make the interface feel like a product professionals could work in for hours: scan, triage, investigate, assign, document and resolve. This is a visual/interaction overhaul, **not a backend rewrite**.

## Verified code locations (as of setup)
- `frontend/src/App.tsx` — app shell, dashboard, activity, team and navigation.
- `frontend/src/incidents.tsx` — queue, case detail, audit timeline.
- `frontend/src/Analyzer.tsx` — CSV analyzer and incident conversion.
- `frontend/src/forms.tsx` — login and reporting.
- `frontend/src/style.css` — most of the styling; an opportunity to split into a coherent tokenized system.
- `frontend/src/api.ts` — typed API client; preserve contracts.

## Morphology over palette
Change the layout **structure** and interaction affordances, not just its accent color. Use the `operations-console` grammar with `enterprise-workbench` morphology. Practical inspiration: precise issue trackers, enterprise admin tools and operational data consoles. Do not copy another company's assets or layout pixel-for-pixel.

- Compact persistent navigation and a practical utility header.
- Tight, deliberate page headings and consistent alignments.
- Flat/slightly elevated panels with 1px rules. No vast boxes around every number.
- Search/filter/action toolbars and structured, readable tables.
- Case-first investigative workflow; facts, status and actionable controls are prominent.
- Semantic color reflects severity/state instead of decorative variety.
- Helpful, understated messages; no generic motivational microcopy.
- Light canvas (white/off-white), charcoal body text and muted slate-blue action family. Inter and clean system fallbacks, monospaced case IDs/log evidence only.
- Avoid glassmorphism, gradients, purple/teal AI color schemes, random stat icons, four identical floating KPI tiles, colorful chart confetti, enormous hero treatments, round bubble navigation and excessive animation.

## Screen-by-screen requirements
1. **App shell:** stable sidebar/navigation, work-context header, clear active section, usable mobile menu. Remove promotional sidebar content. Sign-out and permission context stay discoverable.
2. **Dashboard:** start with operational questions: unresolved/critical work and recent case activity. Use accurate backend metrics with correct definitions and labeled trends; leading content should be actionable. No fabricated live SOC data.
3. **Incident queue:** prioritize scan-and-act. Useful case ID/title, severity, status, assignee, category and updated time. Backend-connected search, filters, sorting, pagination and state counts. Readable density. Clicking rows opens details; keyboard and responsive behavior work.
4. **Investigation detail:** clear case header, metadata, controlled status/severity/assignment, investigation notes as readable narrative, chronological actor-attributed audit trail, transparent confirm/reopen actions. Primary case evidence more prominent than unrelated widgets.
5. **Analyzer:** explain deterministic CSV rule and required format, choose/file/paste input, clear validation errors, evidence-oriented flagged rows, honest distinction between a rule match and actual compromise, conversion to persisted case.
6. **Team & permissions:** compact list and actual permissions, admin action safety. Read-only viewer restrictions enforced by backend as well as UI.
7. **Login:** crisp enterprise login form with labels/focus/error. No fake marketing headline, no production demo credentials exposed in the UI.
8. **System states:** skeleton or stable loading states, meaningful empty queues, retryable failure messages, busy/disabled controls and clear success feedback.

## Engineering tasks
- Start with screenshots of original desktop and mobile UI. Record visual/UX shortcomings with concrete evidence.
- Preserve working backend and API calls. Refactor oversized `App.tsx` and monolithic CSS only as necessary to improve component boundaries. Add semantic CSS tokens for background, surfaces, typography, action, borders, status, radius, spacing, typography and focus.
- Use real server values and valid fake sample data only in seeded demonstration accounts. Avoid cosmetic dummy controls.
- Avoid adopting a large component/UI library if it leads to a generic template look.
- Ensure accessibility (keyboard, focus, errors, target sizes, semantic labels, contrast) and reduced-motion handling.
- Update README/design documentation and checked-in screenshots only after capturing the final implementation.

## Required StyleSeed workflow
If installed: `$styleseed resolve` → read compiled bundle and manifest → `$styleseed build` → `$styleseed score` (target >=80 if executable) → `$styleseed verify` with real browser evidence. Repeat focused corrections up to three passes and report the outcome, including unrun/unavailable commands. Do not claim the score means visual approval. If lock values are unsupported, report the exact field and smallest valid adjustment rather than inventing a successful resolution. Do not automatically run the remote installer; the owner controls installation.

## Acceptance test
- Frontend: npm ci; npm run typecheck; npm run lint; npm test; npm run build.
- Backend: python -m pytest -q; python -m ruff check .
- Browser: login/logout, active nav, create/search/filter/assign/update/resolve/reopen, notes/audit, analyzer and role safety.
- Pixel checks: desktop 1440×900, laptop 1280×800, mobile 390×844; actual captures for Dashboard, Queue, Detail, Analyzer, Team and Login in representative data states.
- No visual regressions, lost functionality or fake claims. PR body includes files, test commands/results, representative screenshots, StyleSeed scored gate and renderer evidence, and honest blockers. Do not push directly to main or automatically merge.

## Final deliverable
A cohesive IncidentOps redesign PR with working responsive UI, verified original functionality, before/after captures, updated README and a concise technical changelog. Owner visually approves before merge.

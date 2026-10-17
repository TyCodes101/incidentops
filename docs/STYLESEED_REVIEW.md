# StyleSeed review — 2026-10-17

Rule set: operations-console × product-ui × saas × dashboard × enterprise-workbench × cobalt-instrument × none. Approved action #315B69 and STYLESEED.md preserved.

## Execution

Loaded installed SKILL.md and ss-build, ss-resolve, ss-score, ss-verify workflows, AGENTS.md and the project redesign brief before editing. Update preflight reported current StyleSeed 5.0.0. The legacy resolver and subsequent --check succeeded. Bundle SHA256: 99582ce8566a5fa719bd9b42083c5b01b4b955db5468beee1a2b60c246accbb2. Build followed the agent workflow against this bundle.

Executed deterministic scanner: `node .agents/skills/styleseed/workflows/ss-score/scripts/styleseed-check.mjs scan --project-root . --all --format json`. **Blocked: SS000, missing .styleseed/project.json**. Resolve/score/verify support this legacy lock, but the scanner requires an artifact registry. [Raw report](verification/styleseed-deterministic.json). No deterministic or typed functional gate pass is claimed.

## Source assessment: 87/100 (B)

This is an agent-applied ss-score rubric assessment of actual source, not a number emitted by the CLI, independent evaluation, or owner acceptance. Per-screen assessments: shell 89; overview/team 87; queue/detail 87; analyzer 89; login/reporting 90. Shared styles are included in each assessment. Lowest-score breakdown:

| Category | Score | Evidence / remaining deductions |
|---|---:|---|
| Color discipline | 16/16 | tokens.css semantic roles; incidents.tsx labeled statuses; locked action preserved. |
| Hierarchy & typography | 13/16 | Bundled Inter and case-first overview. style.css identifier/timeline metadata remains small (10–11px), a readability compromise on lower quality displays. |
| Layout & rhythm | 9/12 | Aligned queue/evidence regions. Detail still has a separate page heading and case heading, increasing vertical travel (App.tsx page-heading; incidents.tsx case-heading). |
| Cards & elevation | 10/10 | Tonal/hairline structure and 4–8px radii; no ornamental metric cards or gradients. |
| States & accessibility | 13/18 | Queue loading/empty/error/retry, detail retry, failed-draft retention, focus, dialog, role guards. workspace.tsx directory and App.tsx activity use shared loading rather than dedicated panel skeletons. |
| Motion & interaction | 6/6 | Instant navigation, short background transitions and reduced-motion override in responsive.css. |
| Coherence | 12/12 | One icon family, shared tokens and repeated control roles. |
| Distinctiveness | 8/10 | Case-first dashboard and audit evidence rail; detail retains conventional stacked summary/notes/history. |

The rubric target is met. The registry-dependent scanner remains blocked; this score does not waive that result.

## Visual verification

Actual Chromium screenshots at 2×: desktop 1440×900, laptop 1280×800, mobile 390×844. Baseline: 21 captures. Final: login, overview, queue, detail, analyzer, team, activity and reporting at all three sizes, plus mobile navigation. Screens use an isolated SQLite demo database. Later captures include synthetic test cases/users, so counts differ from baseline.

First-pass findings repaired and recaptured:
- Sparse team panel stretched into blank space: aligned panels to content height.
- Queue rows too tall: aligned desktop IDs/titles and reduced padding; mobile keeps labeled record fields.
- Mobile analyzer explanation preceded the input: moved supporting rule information below it.
- Activity used only the left of a wide panel: aligned case/action, evidence, actor/time as desktop columns, stacked on mobile.
- Mobile member action wrapped: gave it its own full-width toolbar row.

Major screens were opened and inspected. This review is informed by source review, not blind. No page-level horizontal overflow at the three target sizes. Long mobile collections intentionally scroll vertically. Cross-browser and screen-reader certification are not claimed.

## Functional evidence

Declared outcomes: login/logout; create and persisted case URLs; summary editing and failed-draft retention; status/severity/assignment; notes; resolve/reopen; search/filter/clear; empty/error/retry; CSV import/validation/analysis/conversion; all three roles; mobile navigation/Escape; reduced motion.

The real-API `tests/browser_smoke.py` walkthrough passed all these outcomes with no JavaScript page errors. Frontend regressions cover failed summary drafts and open-only overview requests. These results are not relabeled as StyleSeed's typed Node functional evidence.


## Scoped appearance probe

The installed ss-verify `inspect-appearance.mjs` ran in Chromium at all three target sizes. The first run retained unsupported results for an SVG-containing button text binding and a transparent app-shell background. These are probe limitations, not contrast passes. See [initial observations](verification/appearance-first-pass.json). A subsequent run binds the queue scope subtitle against its opaque panel and the search input boundary against its actual surface, plus the title font. [Final scoped observations](verification/appearance.json). Latin Inter was loaded. These selected pairs and font observations do not establish whole-screen accessibility or glyph coverage for other scripts.

The final mobile appearance probe retains an unsupported scope-subtitle measurement because that desktop-only subtitle is hidden at the narrow breakpoint; the input edge and loaded Latin font observations remain available. This is not reported as a mobile contrast pass for hidden content. Success notices were also scoped to their originating route after screenshot review exposed stale feedback during direct URL navigation.

Final source references: App.tsx:42–72 scopes notices to route changes; incidents.tsx:159–193 handles mutation failures and initial-load retry; incidents.tsx:367 onward preserves API-backed filtering and loading/error/empty states; workspace.tsx:25 onward composes the work queue; tokens.css:1 onward defines the shared visual roles.

The final full browser walkthrough also passed against the production build, including the late account-completion notice regression.

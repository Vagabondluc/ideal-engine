Title: Restore & Enhance World Builder UI (wireframe-driven) — stitch-world-editor-ui-001

Summary
-------
This PR restores and enhances the World Builder UI using the `stitch_world_editor_wireframe` mockup as the visual guide. It focuses on a functional-first implementation that: reintroduces the editor UI with a three-column layout (world tree, editor with interactive gutter, controls), toasts, confirmation modals, AI-assist buttons, versioning, drafts, and an E2E Playwright scaffold.

Key changes
-----------
- src/ui.py — Rebuilt modular Gradio UI, injected APP_STYLE CSS/JS for toasts, gutter, jump-to-line modal, selection sync, and action bridge (retry/open-folder).
- scripts/world_builder.py — persistence helpers, set_debounce exposed, safe action handlers remain and wired to UI.
- Tests: several unit tests and smoke tests under `tests/` (toasts, actions, confirm handlers, visual presence tests).
- E2E: Playwright scaffold under `e2e/playwright/` with smoke and flow tests (`editor.spec.ts`, `editor_flow.spec.ts`) and helper `scripts/start_test_app.py` to run app for tests.
- OpenSpec: added change proposal and spec delta under `openspec/changes/stitch-world-editor-ui-001/` (proposal.md, tasks.md, design.md, specs/ui/spec.md) and validated the change.

Screenshots / Mockups
---------------------
- Wireframe mockups are available under `stitch_world_editor_wireframe/` (use `world_editor_wireframe/screen.png` for visuals).
- Add or record additional screenshots after running the app locally for final PR screenshot assets.

How to run tests
----------------
- Unit tests: `python -m pytest -q` (all tests passing locally)
- E2E (local):
  1. Start test app: `python scripts/start_test_app.py` (binds to http://127.0.0.1:7870)
  2. In `e2e/playwright`: `npm ci` and `npx playwright install`
  3. Run: `npx playwright test`

PR checklist
------------
- [ ] Unit tests pass
- [ ] Playwright E2E smoke runs locally
- [ ] Screenshot(s) added to the PR
- [ ] OpenSpec validation passes (`openspec validate stitch-world-editor-ui-001 --strict`)

Notes for reviewer
------------------
- The interactive gutter is implemented with best-effort DOM heuristics to support Gradio's rendered editor (textarea or content wrappers). For advanced editor integration (CodeMirror, Monaco), we'll add adapter hooks in follow-up work.
- E2E Playwright tests are conservative; they rely on the presence of a textarea in `#wb-editor`. If your environment uses a different renderer, the tests will skip or may require minor selector adjustments.

Suggested branch name: `stitch-world-editor-ui-001`
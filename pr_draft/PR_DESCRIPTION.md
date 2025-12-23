PR Title
========
Restore & Enhance World Builder UI — stitch-world-editor-ui-001

One-line summary
----------------
Reintroduce core World Builder UI features (editor, gutter, toasts, modals, versioning) with tests and Playwright E2E scaffold.

Detailed description
--------------------
This change decomposes the existing editor monolith and implements a modular, testable Gradio-based UI in `src/ui.py`. It restores critical features from the legacy UI and introduces:
- **UI Contract Enforcement**: Hard separation between `Generate` (low safety) and `World Editor` (high safety) modes via Tabs.
- Toast notifications (show_toast)
- Confirmation and retry flows (action bridge + `wb-action-box`)
- Versioning and draft persistence (`save_new_version`, `persist_draft`, `revert_editor`) with metadata files
- Interactive line gutter with clickable lines and selection/scroll sync
- Keyboard Jump-to-line (Ctrl/Cmd+G) modal
- **Autonomous src/**: All logic (indexer, runner, watcher, world_builder) migrated to `src/` for a clean package structure.
- E2E Playwright test harness + helper `src/start_test_app.py` to run app on port 7870

Files changed / added (high level)
----------------------------------
- src/ui.py (new/major changes)
- src/world_builder.py (domain logic)
- src/ollama_runner.py (model execution)
- src/start_test_app.py (E2E helper)
- openspec/changes/stitch-world-editor-ui-001/* (spec + proposal)
- tests/* (new unit tests covering UI handlers and visual presence)
- e2e/playwright/* (Playwright scaffold & tests)
- .github/workflows/e2e-playwright.yml (CI scaffold for E2E)

Testing notes
-------------
- Unit tests were executed locally and are passing (35 tests).
- OpenSpec validation: passed after shifting Gradio launch port to 7861 for strict validation.
- E2E tests are scaffolded; please run locally or in CI (requires Node & Playwright). `src/start_test_app.py` will run the app on port 7870 for testing.

How to reproduce locally
------------------------
1. Create a branch (suggested): `git checkout -b stitch-world-editor-ui-001`
2. Run `python -m pytest` (unit tests)
3. Start app for Playwright: `python -m src.start_test_app`
4. In `e2e/playwright`: `npm ci && npx playwright install && npx playwright test`

Follow-up items
----------------
- Replace textarea heuristics with an editor adapter to support Monaco/CodeMirror.
- Add more E2E scenarios (save->version->restore, AI-assist end-to-end with a local model)
- Performance analysis on very large world files (>2MB) and streaming improvement for the console

If you want, I can initialize a Git branch and create the PR draft using GitHub CLI — tell me the remote and whether you'd like me to push from here.
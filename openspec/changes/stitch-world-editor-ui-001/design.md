# Design notes for stitch-world-editor-ui-001

This document captures architectural reasoning, interactions between components, and trade-offs.

High-level architecture
-----------------------
- UI layer: `src/ui.py` (Gradio Blocks) — mounts layout and wires handlers.
- Domain logic: `scripts/world_builder.py` — persistence, versions, drafts, action handlers.
- Runner: `src/runner.py` — Ollama runner wrapper; AI-assist flows use this.
- Tests: `tests/*` — unit tests for Python handlers, smoke tests for `create_app()`. E2E tests to run against running Gradio app.

Client-side interactions
------------------------
- A small JS module is injected via `APP_STYLE` to implement toasts, the gutter sync/selection, JS→Python bridge (writing JSON to hidden `wb-action-box` Textbox), and confirm modal interaction flows.
- The gutter implementation is best-effort and robust: it supports textarea/input and common code rendering containers; for advanced editor integration (Monaco/CodeMirror), we will create adapter hooks in a follow-up.

Safety & sandboxing
--------------------
- `open_folder` must be restricted to workspace `.` and `world_db` subtree (already implemented server-side in `scripts/world_builder.open_folder`). UI will not override these checks.
- Retry flows should use `RETRY_REGISTRY` with opaque retry IDs; UI only repeats the retry request by providing the retry id.

Test strategy
-------------
- Unit tests: purely server-side tests for handlers (save, save_new_version, confirm handlers, action dispatch). Use monkeypatching for the runner and file system as needed.
- Integration smoke test: `tests/test_ui_smoke.py` calls `create_app()` and exercises `run_model` with a stubbed runner.
- E2E: Playwright script (follow-up) to click through the UI and assert visual state changes (gutter highlight, selection) and that the server side produced files/versions.

Trade-offs
----------
- Client-side best-effort vs precise integration: using DOM sniffing is less accurate than editor APIs but avoids adding a heavy editor dependency in this change. If we later add CodeMirror/Monaco, we will add adapters.
- Visual fidelity: we prioritize functional parity first; fully pixel-perfect styling should be a separate follow-up task.

Operational notes
-----------------
- Add a short `CHANGELOG.md` entry describing this change once merged.
- Document how to run the app locally and run E2E tests in `openspec/changes/stitch-world-editor-ui-001/tasks.md`.

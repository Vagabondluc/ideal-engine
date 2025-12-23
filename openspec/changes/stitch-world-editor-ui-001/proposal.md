# Proposal: stitch-world-editor-ui-001 — Restore & Improve World Editor UI (wireframe-driven)

Change ID: stitch-world-editor-ui-001

Author: GitHub Copilot (on behalf of workspace owner)

Status: Draft

Summary
-------
Implement a functional-first restoration and enhancement of the World Editor UI using the provided mockup assets in `stitch_world_editor_wireframe/` as the visual reference. This change focuses on restoring behavior from the legacy `scripts/world_builder.py` while aligning the layout and interactive affordances with the wireframe (tree/editor/controls, toasts, confirmations, AI-assist, versions, line gutter interactivity).

Goals
-----
- Restore the core editor flows (select → edit → save → save-version → load-version → revert → drafts) so the app is functional and testable.
- Use the `stitch_world_editor_wireframe` HTML assets as the authoritative visual mockup for layout, component placement, and behavior expectations.
- Prioritize a minimal, robust implementation ("functional-first") that is easy to test and iterate on; provide a separate, scoped follow-up for pixel-perfect styling.

Scope
-----
Included:
- Rebuild UI in `src/ui.py` with layout parity (left: tree, center: editor with gutter, right: controls) and the interactive features in the wireframe.
- Inject lightweight CSS/JS to approximate the mockup appearance and provide robust client-side interactions (gutter syncing, clickable lines, toasts, confirmation modal, action bridge for retry/open-folder).
- Add unit tests and integration smoke tests (create_app + core handlers) and plan for E2E tests.

Excluded (out of scope for this change):
- Heavy-weight visual theming (no Tailwind dependency).
- Full code-editor integration with Monaco/CodeMirror advanced APIs (can be added in follow-up with adapter patterns).

Acceptance Criteria (high level)
------------------------------
1. Core application flows are implemented and covered by tests: save, save-new-version (with notes), load-version, restore-draft, revert.
2. The UI layout is functionally consistent with the wireframe (three-column layout, visible controls) and includes: toaster, confirmation modal, AI-assist buttons, debounce and auto-refresh, and versions dropdown.
3. The gutter is interactive: line counts update with editor content, clicking a line selects the corresponding line in the editor, and selection highlights the corresponding gutter lines.
4. The JS→Python action bridge (`wb-action-box`) supports retry and open-folder actions and is covered by unit tests.
5. Automated tests (unit + smoke) pass for the new behaviors.

Dependencies & Risks
--------------------
- The Ollama runner availability affects some AI-assist flows; these are stubbed in unit tests and have safe failure modes.
- Browser variations (embedding Gradio code objects) require the client-side JS to be robust and best-effort; precise editor behavior for advanced editors may need adapter code in follow-up work.

References
----------
- Mockup assets: `stitch_world_editor_wireframe/` (HTML + screenshots)
- Existing mapping: `openspec/changes/ui-wireframe-mapping.md`
- Current implementation in progress: `src/ui.py`, `scripts/world_builder.py`

Questions / Clarifications
-------------------------
- Confirm whether you want Playwright-based E2E tests included in this change or as a follow-up task (recommended follow-up).
- Any additional accessibility expectations (keyboard-only flows, ARIA) beyond the basic keyboard navigation? If so, we should add detailed A11y requirements.

Next steps
----------
If this proposal looks good I'll convert it into spec deltas and an ordered `tasks.md` and `design.md` capturing the architecture and validation details.
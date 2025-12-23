# UI Wireframe → Implementation Mapping

Source: `stitch_world_editor_wireframe/world_editor_wireframe`

Goal: Implement a **functional-first** UI that matches the wireframe layout and restores the features from the previous `world_builder.py`. Visual polishing is a follow-up task.

## Components & Mapping

- Left column — "World Database"
  - Wireframe: tree view with actions (download/copy) and a select entry input
  - Implementation: `src/ui.py`: `world_tree` (gr.Code), `file_select` (gr.Dropdown). Add helper to render a tree-like string. Add buttons for refresh and copy-download stubs.

- Center — "Markdown Editor"
  - Wireframe: line gutter, big textarea, Save / Save New Version / Revert buttons
  - Implementation: `src/ui.py`: `editor` (gr.Code), `save_btn`, `save_version_btn`, `revert_btn`. Implement draft persistence (`persist_draft`), save (`save_editor`), revert (`revert_editor`). For line numbers, add a simple gutter marker (non-functional) as an optional polish.

- Right column — Controls, AI Assist, Auto-refresh, Debounce
  - Wireframe: AI assist grid, auto-refresh toggle + debounce slider, last refreshed
  - Implementation: map AI Assist buttons to `wb.ai_assist_action` via `src/ui._on_ai_assist`. Add `auto-refresh` state, debounce slider connected to `wb.set_debounce` (or local state). Add `last_refreshed` text updated by `check_for_updates`.

- Global elements
  - Toasts: inject `TOAST_SCRIPT` + `show_toast` helper (already present) ✅
  - Confirmation modal: pending action state and confirm/cancel handlers (`pending_action`, `confirm_yes`, `confirm_no`) ✅
  - JS → Python action bridge: hidden `wb-action-box` (elem_id='wb-action-box') and `handle_action_json` handler for `retry` and `open_folder` actions ✅

## Acceptance Criteria

1. Core flows work end-to-end in a local run: select file → edit → save → save new version (with notes) → load version → restore draft → revert. (tests or smoke script)
2. Toasts appear for success/failure and errors include action buttons (Retry / Open containing folder) that trigger Python handlers via the hidden action box.
3. AI assist buttons call `wb.ai_assist_action` and return suggestion text and a toast.
4. JS → Python bridge is testable via `tests/test_ui_actions.py` (simulate JSON payloads) and has unit tests for `retry` and `open_folder` flows.

## Next steps (implementation order)

1. Create this mapping (done).
2. Implement the functional-first layout in `src/ui.py` (structure + handlers).
3. Add unit tests for the confirmation modal and JS action bridge.
4. Add a small integration smoke test that asserts `create_app()` mounts core elements.
5. Polish visuals to match the wireframe as a separate PR/task.

---

Notes:
- For safety, `open_folder` must remain restricted to workspace and `world_db` subtree (already enforced in `scripts/world_builder.py`).
- The wireframe uses Tailwind styling — we will approximate using Gradio's layout and lightweight injected CSS rather than adding Tailwind as a dependency.

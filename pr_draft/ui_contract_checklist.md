# UI Contract Checklist — stitch-world-editor-ui-001

This is a machine-readable checklist (JSON in `ui_contract_checklist.json`) and a short human summary to guide implementation.

## How to use

- Coding AI: ingest `pr_draft/ui_contract_checklist.json` and run automated checks against rendered UI tree and integration tests.
- Humans: follow the **GLOBAL RULE**: only two modes (Generate, World Editor) and **never mix controls** unless listed.

## Quick checks (human)

- Mode separation:
  - Generate mode shows: Prompt, Run, Output, Promote only
  - World Editor shows: Editor, Save/Versions, Context Banner, AI Assist (selection-only)
- Explorer hides internal files by default; advanced toggle reveals them
- AI Assist returns diffs and never auto-applies
- Dirty-state guard prevents navigation without confirmation

## Recommended acceptance tests

- Generate mode UX:
  - Banner visible: "Mode: Generate — Output is NOT saved unless promoted"
  - Running model doesn't change canon automatically
- World Editor UX:
  - Context banner shows file path, version, and modified state
  - Save/Save as New Version are gated by dirty state
  - AI Assist returns a diff and only applies after explicit confirmation
- Explorer UX:
  - Internals hidden by default; Advanced toggle reveals internals

## Next actions

1. Implement Phase 1 (tab separation) and keep all existing behaviors behind the correct modes
2. Add static checks (unit tests) that fail if a control appears in the wrong mode
3. Add E2E tests to validate flows described in the JSON

---

If you want, I can now:

- Convert each JSON acceptance test to executable unit/e2e tests and open a PR with the changes, or
- Generate a single corrective prompt to refactor `src/ui.py` to obey this checklist automatically.

Tell me which next step you prefer (I or II).
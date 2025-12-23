# Tasks for stitch-world-editor-ui-001

This is an ordered list of small, verifiable tasks to deliver the UI change incrementally. Each task includes validation guidance (tests or manual checks).

1. Draft proposal (this file) and get buy-in from stakeholders. (Validation: proposal.md approved)
2. Create a spec delta describing functional requirements for the UI (`specs/ui/spec.md`). (Validation: spec.md includes ADDED requirements and scenarios)
3. Implement functional layout: three-column Gradio layout with world tree, editor with gutter, and controls. (Validation: `create_app()` smoke test mounts columns and components)
4. Implement editor core flows: select → load → edit → save → save new version (notes) → load-version → revert → restore draft. (Validation: unit tests exist and pass)
5. Add toasts and confirmation modal flows; ensure confirm/cancel handlers are testable. (Validation: unit tests for confirm handlers pass)
6. Implement JS→Python action bridge (`wb-action-box`) and tests for `retry` and `open_folder`. (Validation: unit tests simulate payloads)
7. Implement interactive gutter and selection sync (click to select line; highlight line on selection). (Validation: client-side smoke test and JS injection tests)
8. Add Auto-refresh + Debounce control and wire to `scripts/world_builder.set_debounce`. (Validation: toggles produce toasts and the debounce stub returns scripts/messages)
9. Add unit and small integration tests for all new features (modal flows, gutter presence, confirm flows). (Validation: `pytest` green)
10. Add E2E test plan (Playwright) and scaffold Playwright harness (package.json, config, basic test). Validation: Playwright test scaffold passes locally against a started test app and smoke test executes.
11. Performance test for large files (document limit recommendations and behavior). (Validation: documented results and adjustable polling interval)
12. Prepare PR with screenshots and changelog entry. (Validation: PR checklist completed)

Notes:
- Keep tasks small and test-driven. Tasks 7 and 10 are potential places where iterative usability feedback may change scope.

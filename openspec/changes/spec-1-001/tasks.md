```markdown
1. Review PRD and confirm scope in `proposal.md`.
2. Create `design.md` documenting index format, storage layout, and watcher behavior.
3. Implement UI wiring plan (Gradio components list and data flows) in `design.md`.
4. Draft spec delta `specs/spec-1/spec.md` covering browsing, preview, copy/append, save-as-new-version, index regeneration, and live reload scenarios.
5. Run `openspec validate spec-1-001 --strict` and iterate until clean.
6. Ask for proposal approval before moving to implementation.

Validation: Each task must map to a verifiable check (index format example, watch test scenario, or UI component list).

```

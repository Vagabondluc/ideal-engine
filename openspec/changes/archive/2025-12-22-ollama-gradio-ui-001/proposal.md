# Change: ollama-gradio-ui-001

## Summary

Add a lightweight Gradio-based web interface for the existing `scripts/ollama_runner.py` runner. The UI will let users configure backend (CLI / Python / HTTP), pick or upload a prompt from the `Narrative Scripts/` hierarchy, select a model, and view streamed or final outputs in a friendly web UI.

## Motivation

While the CLI/interactive menus work well for local development, a web UI lowers the entry barrier for non-terminal users and enables rapid experimentation with models and prompt files. Gradio provides an easy-to-run local UI that integrates cleanly with the Python codebase.

## Scope

- Provide a proposal, tasks, design, and spec delta (this change).
- Implementation (post-approval) will deliver:
  - `scripts/ollama_gradio.py` — a small Gradio app that imports and reuses `scripts/ollama_runner` internals where appropriate.
  - UI components for selecting backend, specifying endpoint/host, picking model, choosing a prompt from the `Narrative Scripts/` folder (hierarchical browser), or uploading a file.
  - Support for streamed outputs when supported by the selected backend (show incremental output in UI).
  - Minimal installation instructions and requirements (e.g., `gradio` entry in `requirements-ollama-runner.txt` or a new `requirements-ollama-gradio.txt`).

## Non-Goals

- Replacing the runner CLI; CLI and Gradio UI co-exist.
- Long-lived web deployment, authentication, or remote hosting models beyond local Gradio usage.

## Deliverables

- `openspec/changes/ollama-gradio-ui-001/{proposal.md,tasks.md,design.md}`
- `openspec/changes/ollama-gradio-ui-001/specs/gradio-ui/spec.md`
- Implementation files (post-approval): `scripts/ollama_gradio.py`, `requirements-ollama-gradio.txt`, small README additions and tests.

## Acceptance Criteria

- The Gradio app runs locally with `python scripts/ollama_gradio.py` and serves a UI on an accessible port.
- Users can select a backend, choose a model, pick a prompt from `Narrative Scripts/` (hierarchical browser) or upload one, run the prompt, and see the model output.
- Streaming output appears incrementally when the backend supports it.

## Next Steps

1. Approve this proposal.
2. Implement the Gradio app following `tasks.md` and `design.md`.
3. Validate with local tests and `openspec validate`.

## Why

Providing a Gradio UI makes the Ollama runner accessible to non-terminal users, speeds up experimentation, and offers a concise visual workflow for selecting models and prompt files.

## What Changes

- Adds a Gradio app entrypoint that reuses the existing runner logic.
- Adds a small requirements file and README documenting how to run the UI.
- Adds OpenSpec spec delta describing the UI requirements and acceptance scenarios.

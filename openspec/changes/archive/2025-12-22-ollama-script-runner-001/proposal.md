# Change: ollama-script-runner-001

## Summary

Add an "Ollama runner" capability: a small, cross-platform script that lets a user choose which Ollama model to load and send a request using any prompt/script file from the Narrative Scripts/ folder.

## Motivation

Team members often want to experiment with different local Ollama models and quickly run existing narrative prompt files. A tiny runner reduces friction and standardizes invocation.

## Scope

- Provide a proposal, tasks, design, and spec deltas (this change).
- Implementation will produce a single script (Python) that:
  - lists available Ollama models (or accepts a model name),
  - lists available prompt files under `Narrative Scripts/`,
  - sends the chosen prompt to the chosen model using the Ollama CLI/HTTP endpoint,
  - prints model output to stdout and returns sensible exit codes.

## Non-Goals

- Replacing existing tooling or adding complex orchestration.
- Deploying models or managing Ollama installation; the runner will detect and error clearly if Ollama is missing.

## Deliverables

- `openspec/changes/ollama-script-runner-001/{proposal.md,tasks.md,design.md}`
- `openspec/changes/ollama-script-runner-001/specs/ollama-runner/spec.md`
- (Implementation planned but not included in this proposal stage)

## Acceptance Criteria

- The proposal and spec validate with `openspec validate <id> --strict` (no failures).
- The implementation (after approval) will satisfy the spec scenarios.

## Risks & Questions

- Do we prefer a PowerShell-first implementation for Windows users, or a cross-platform Python script? (Design recommends Python for cross-platform parity.)
- Should the script support both Ollama local CLI and Ollama HTTP API endpoints? (Design documents tradeoffs.)

## Next Steps

1. Approve this proposal.
2. Implement the script according to `tasks.md` and `design.md`.
3. Validate with `openspec validate` and run local tests.

## Why

This runner centralizes how developers invoke local Ollama models against existing narrative prompts, reducing manual CLI usage and making experimentation reproducible.

## What Changes

- Adds a cross-platform Python script to list models, choose prompts from `Narrative Scripts/`, and run prompts via CLI, HTTP, or Python client.
- Adds tests, README, and a minimal requirements file for the runner.
- Adds an OpenSpec spec delta describing the runner capability and acceptance scenarios.

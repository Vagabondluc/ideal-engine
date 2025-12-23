# Project Context

## Purpose
A modular world-building and narrative generation tool using Ollama and Gradio.

## Tech Stack
- Python 3.11
- Gradio (UI)
- Ollama (LLM Inference)
- Pytest (Unit Testing)
- Playwright (E2E Testing)

## Project Conventions

### Code Style
- Modular Python code in `src/`.
- Absolute imports from `src` or relative imports within the package.
- HTML/JS injection for advanced Gradio features (toasts, gutters).

### Architecture Patterns
- **Autonomous `src/`**: All core logic resides in `src/`. `scripts/` is legacy.
- **UI Contract**: Hard separation between `Generate` (low safety) and `World Editor` (high safety) modes using Tabs.
- **Domain Logic**: Separated into `indexer.py`, `runner.py`, `world_builder.py`, and `ollama_runner.py`.

### Testing Strategy
- Unit tests in `tests/` using `pytest`.
- E2E tests in `tests/e2e/` using `playwright`.
- Mocking of subprocess and filesystem for unit tests.

### Git Workflow
- OpenSpec for change proposals and validation.

## Domain Context
- **World Database**: A collection of Markdown files in `world_db/`.
- **Narrative Scripts**: Prompt templates in `Narrative Scripts/`.
- **Versioning**: Immutable versions stored in `world_db/.versions/`.
- **Drafts**: Autosaved drafts in `world_db/.drafts/`.

## Important Constraints
- `Generate` mode must not auto-save to canon.
- `World Editor` mode must maintain "canonical truth" with explicit save actions.
- File operations restricted to workspace and `world_db/`.

## External Dependencies
- Ollama (local LLM server).
- Gradio (web UI framework).


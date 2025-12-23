# Design: Gradio interface for Ollama runner

## Goals

- Provide a simple, local Gradio UI to configure backend, pick or upload prompt files, select models, and display outputs (including streaming).
- Reuse `scripts/ollama_runner` core functions to avoid duplication and leverage existing CLI/HTTP/Python client logic.

## UI Layout

- Top bar: Backend selection (`cli` / `python` / `http`), and conditional inputs:
  - `cli`: no extra fields
  - `python`: `Host` input (optional)
  - `http`: `Endpoint` input (required)
- Model selector: dropdown populated from `ollama list` (CLI) or `ollama.list()` (Python client) or cache. Refresh button available.
- Prompt selection area:
  - Left pane: hierarchical browser of `Narrative Scripts/` (folder tree). Clicking a file loads it into the editor.
  - Right pane: text editor showing prompt contents (editable). Also an upload button to load an external file.
- Execution controls: `Run` button, `Stream` toggle.
- Output area: scrollable text box that appends streaming chunks; `Save output` button.

## Backend integration

- Prefer reusing `scripts/ollama_runner` functions where possible:
  - Model listing: call `list_models_cli()` or `ollama.list()` and normalize outputs using `extract_model_name()`.
  - Prompt reading: use `read_prompt()` and directory traversal functions for the browser.
  - For CLI backend, run `call_ollama_cli()` in a background thread, capturing stdout/stderr and forwarding to UI. Use `subprocess.Popen` for incremental reads.
  - For Python client backend, call `call_ollama_python()` with `stream=True` and yield chunks to the UI.
  - For HTTP backend, use `call_ollama_http()` in a thread and update UI on completion.

## Streaming

- For streaming, the Gradio component should consume an iterator/generator and append incoming text to the output area.
- If the backend doesn't support streaming, fall back to running and then display the final output.

## Concurrency and responsiveness

- All model calls must run off the main Gradio thread (background threads or async) to avoid blocking the UI.

## Security & safety

- The UI runs locally only. Warn users when using HTTP endpoints that prompts will be sent over the network.
- Do not persist prompt files or outputs by default (allow user to save explicitly).

## Files to create

- `scripts/ollama_gradio.py` — the Gradio app entry point.
- `requirements-ollama-gradio.txt` — minimal dependencies (`gradio`, optional `ollama` if desired).
- `README_OLLAMA_GRADIO.md` — quick start guide.

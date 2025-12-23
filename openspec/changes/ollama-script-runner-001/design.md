```markdown
# Design: Ollama runner

## Goals

- Small, cross-platform runner implemented in Python 3.9+.
- Minimal dependencies (std library + `requests` if HTTP API used).
- Usable interactively and in scripts (CLI args + optional interactive prompts).

## High-level flow

1. Parse CLI args: `--model`, `--prompt`, `--list-models`, `--list-prompts`, `--endpoint`.
2. If `--list-models` call `ollama` CLI (`ollama list`) or query endpoint.
3. If no `--prompt` provided, list files under `Narrative Scripts/` and let user choose.
4. Read prompt file; pass contents to Ollama:
   - Preferred: call `ollama` CLI with subprocess for streaming/compatibility.
   - Fallback: use Ollama HTTP API (if user provides `--endpoint`).
5. Print output to stdout; provide `--out-file` to capture.

## Implementation notes

- Use `subprocess.run` or `subprocess.Popen` to invoke `ollama` CLI. Provide clear error messages when the binary is missing.
- Keep CLI UX simple; support non-interactive usage for automation.
- For Windows, Python script invocation is `python scripts/ollama_runner.py ...` and an optional `ollama-run.ps1` shim can be added later.

## Security & safety

- Treat prompt files as local files only; do not upload them anywhere by default.
- If using HTTP endpoint, warn the user and require explicit `--endpoint`.

## Files to create at implementation

- `scripts/ollama_runner.py` — main script
- `tests/test_runner.py` — basic unit tests
- `README.md` — usage examples

```
# Design: Ollama runner

## Goals

- Small, cross-platform runner implemented in Python 3.9+.
- Minimal dependencies (std library + `requests` if HTTP API used).
- Usable interactively and in scripts (CLI args + optional interactive prompts).

## High-level flow

1. Parse CLI args: `--model`, `--prompt`, `--list-models`, `--list-prompts`, `--endpoint`.
2. If `--list-models` call `ollama` CLI (`ollama list`) or query endpoint.
3. If no `--prompt` provided, list files under `Narrative Scripts/` and let user choose.
4. Read prompt file; pass contents to Ollama:
   - Preferred: call `ollama` CLI with subprocess for streaming/compatibility.
   - Fallback: use Ollama HTTP API (if user provides `--endpoint`).
5. Print output to stdout; provide `--out-file` to capture.

## Implementation notes

- Use `subprocess.run` or `subprocess.Popen` to invoke `ollama` CLI. Provide clear error messages when the binary is missing.
- Keep CLI UX simple; support non-interactive usage for automation.
- For Windows, Python script invocation is `python scripts/ollama_runner.py ...` and an optional `ollama-run.ps1` shim can be added later.

## Security & safety

- Treat prompt files as local files only; do not upload them anywhere by default.
- If using HTTP endpoint, warn the user and require explicit `--endpoint`.

## Files to create at implementation

- `scripts/ollama_runner.py` — main script
- `tests/test_runner.py` — basic unit tests
- `README.md` — usage examples

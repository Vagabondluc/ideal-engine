```markdown
1. Draft proposal (`proposal.md`) and get stakeholder approval.
2. Create design notes (`design.md`) with chosen approach and trade-offs.
3. Implement the runner script (`scripts/ollama_runner.py`) — cross-platform Python.
   - Detect Ollama availability (CLI or HTTP endpoint).
   - Enumerate models or accept a `--model` argument.
   - Enumerate prompt files under `Narrative Scripts/` or accept `--prompt` path.
   - Stream or capture model output and print to stdout.
   - Return non-zero exit codes on error.
4. Add minimal tests: invocation tests and missing-dependency tests.
5. Document usage in `README.md` and add quick examples.
6. Run `openspec validate ollama-script-runner-001 --strict` and iterate until clean.

Validation: each task should have a verification step (unit or manual check) and a test or instruction to reproduce.

```
1. Draft proposal (`proposal.md`) and get stakeholder approval.
2. Create design notes (`design.md`) with chosen approach and trade-offs.
3. Implement the runner script (`scripts/ollama_runner.py`) — cross-platform Python.
   - Detect Ollama availability (CLI or HTTP endpoint).
   - Enumerate models or accept a `--model` argument.
   - Enumerate prompt files under `Narrative Scripts/` or accept `--prompt` path.
   - Stream or capture model output and print to stdout.
   - Return non-zero exit codes on error.
4. Add minimal tests: invocation tests and missing-dependency tests.
5. Document usage in `README.md` and add quick examples.
6. Run `openspec validate ollama-script-runner-001 --strict` and iterate until clean.

Validation: each task should have a verification step (unit or manual check) and a test or instruction to reproduce.

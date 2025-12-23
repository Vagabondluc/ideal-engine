1. Draft proposal (`proposal.md`) and get stakeholder approval.
2. Create `design.md` with UI layout, interactions, and backend integration notes.
3. Implement `scripts/ollama_gradio.py` that:
   - Reuses `scripts/ollama_runner` functions (model listing, prompt reading, backends) where practical.
   - Provides UI controls: backend selector, endpoint/host input, model selector, prompt browser/upload, run button, streaming output area.
   - Runs model calls in background threads to keep UI responsive.
4. Add `requirements-ollama-gradio.txt` (includes `gradio` and `ollama` if needed) and update README with quick-start instructions.
5. Add basic tests that the Gradio app starts and the model invocation function behaves correctly with mocked backends.
6. Run `openspec validate ollama-gradio-ui-001 --strict` and iterate until clean.

Validation notes:
- Manual test: start the app and run a sample prompt with each backend.
- Unit test: mock backends (CLI/HTTP/Python) and assert output pipeline works and streams when requested.

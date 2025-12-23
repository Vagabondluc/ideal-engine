## ADDED Requirements

### Requirement: Gradio UI app
- The repository MUST include a Gradio-based UI that allows users to configure the Ollama backend, choose a model, select or upload a prompt from the `Narrative Scripts/` folder, run the prompt, and view model output.

#### Scenario: Start UI
- Given a developer runs `python scripts/ollama_gradio.py`, the Gradio app starts and serves a local web UI. The UI page loads in the browser and shows backend, model, prompt browser, and output area.

#### Scenario: Configure backend and run
- Given the UI is open and the user selects `python` client and a host, picks a model, and selects a prompt from the browser, when they click `Run` with `Stream` enabled, the UI displays incremental output as it arrives; if streaming is unsupported, UI shows final output when available.

#### Scenario: Upload prompt
- Given the user uploads a file via the UI, the file contents are loaded into the editor and can be run like any chosen prompt.

#### Scenario: Model list refresh
- Given the user clicks `Refresh models`, the UI refreshes the model dropdown using the selected backend and shows an error if models cannot be listed.

#### Scenario: Security warning
- Given the user chooses `http` backend and provides an endpoint, the UI shows a warning that prompt contents will be sent over the network before allowing the run.

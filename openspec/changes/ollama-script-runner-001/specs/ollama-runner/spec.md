```markdown
## ADDED Requirements

### Requirement: ollama-runner script
- The repository MUST include a runnable script that lets a user choose an Ollama model and a prompt file from `Narrative Scripts/` and send the prompt to the model.

#### Scenario: List prompts and run interactively
- Given the user runs the script without `--prompt`, the script lists files under `Narrative Scripts/` and lets the user choose one.
- When the user picks a file and a model, the script sends the file contents to the model and prints the output.

#### Scenario: Non-interactive invocation
- Given the user supplies `--prompt path/to/file` and `--model MODEL_NAME`, the script runs without prompting and returns the model output to stdout.

#### Scenario: Ollama missing
- Given the user has no `ollama` CLI and no HTTP endpoint provided, the script exits with code 2 and prints a clear message explaining installation options.

#### Scenario: Using HTTP endpoint
- Given the user specifies `--endpoint http://host:11434`, the script uses the HTTP API to send the prompt (and warns about sending files over network).

#### Scenario: Exit codes
- Exit code 0: success
- Exit code 1: runtime error while running model (e.g., model error)
- Exit code 2: precondition error (e.g., missing Ollama binary and no endpoint)

```
## ADDED Requirements

### Requirement: ollama-runner script
- The repository MUST include a runnable script that lets a user choose an Ollama model and a prompt file from `Narrative Scripts/` and send the prompt to the model.

#### Scenario: List prompts and run interactively
- Given the user runs the script without `--prompt`, the script lists files under `Narrative Scripts/` and lets the user choose one.
- When the user picks a file and a model, the script sends the file contents to the model and prints the output.

#### Scenario: Non-interactive invocation
- Given the user supplies `--prompt path/to/file` and `--model MODEL_NAME`, the script runs without prompting and returns the model output to stdout.

#### Scenario: Ollama missing
- Given the user has no `ollama` CLI and no HTTP endpoint provided, the script exits with code 2 and prints a clear message explaining installation options.

#### Scenario: Using HTTP endpoint
- Given the user specifies `--endpoint http://host:11434`, the script uses the HTTP API to send the prompt (and warns about sending files over network).

#### Scenario: Exit codes
- Exit code 0: success
- Exit code 1: runtime error while running model (e.g., model error)
- Exit code 2: precondition error (e.g., missing Ollama binary and no endpoint)

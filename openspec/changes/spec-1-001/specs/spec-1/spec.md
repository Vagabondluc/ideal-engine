```markdown
## ADDED Requirements

### Requirement: Script Browser & Versioned Prompt Workspace
- The repository MUST provide a Gradio-based UI that allows users to browse canonical scripts by category, preview file contents verbatim, copy or append canonical scripts into an editable prompt workspace, and save edited prompts as new immutable versions.

#### Scenario: Browse and preview
- Given the index is generated, when the user selects a category and chooses a script, the UI shows a read-only preview containing the verbatim contents of the canonical script.

#### Scenario: Copy and append verbatim
- Given a canonical script is selected, when the user clicks `Copy → Prompt` the prompt editor is replaced with the script contents exactly byte-for-byte.
- Given a canonical script is selected, when the user clicks `Append → Prompt` the script contents are appended to the prompt editor separated by a clear delimiter.

#### Scenario: Save as new version
- Given an edited prompt in the workspace, when the user chooses `Save as New Version` and confirms metadata, the system writes a new file under `scripts/versions/<category>/<script>/v{n}.txt` and updates `index.json` with version metadata.

#### Scenario: Live reload
- Given a developer modifies files under `scripts/canonical/` on disk, the indexer rebuilds `index.json` and the UI refreshes lists and previews without restarting the application.

#### Scenario: Index integrity
- The `index.json` MUST include script id, category, canonical path, version list, and metadata. The index can be regenerated at any time from the storage layout and the UI must read only from this index.

#### Scenario: Safety
- The system MUST never modify files under `scripts/canonical/`. All user-created content must be stored under `scripts/versions/` or `scripts/drafts/`.

```

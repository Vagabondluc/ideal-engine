# Spec: UI — stitch-world-editor-ui-001

## ADDED Requirements

### Requirement: Functional-first World Editor UI
- The system SHALL provide a three-column editor UI with: a left column showing a world database tree and file selector, a center column containing a markdown editor (with line-number gutter), and a right column with controls (AI Assist buttons, auto-refresh toggle, debounce slider, last-refreshed indicator, activity log).

#### Scenario: Save flow
- Given a file `relpath` is selected
- When the user edits content and clicks Save
- Then the server SHALL call `scripts.world_builder.save_editor(relpath, content)` and return a toast indicating success or an error message when it fails.

#### Scenario: Save New Version with notes
- Given `relpath` is selected and user opened Save-as-New-Version
- When user provides notes and confirms
- Then the system SHALL write a new version file under `.versions/<relpath>/v_<ts>.md` and a metadata file `v_<ts>.md.meta.json` with `notes` and `timestamp`.

### Requirement: Interactive gutter
- The system SHALL display the correct number of lines in the gutter synchronized with the editor content and update on content changes.
- The system SHOULD allow clicking a gutter line to select that entire line in the editor (best-effort across editor implementations).

#### Scenario: Retry & Open Folder via Action Bridge
- Given the UI displays an error with a Retry button (contains `data-retry-id`) or Open folder button (contains `data-open-folder`)
- When the user clicks the button
- Then the client SHALL write a JSON payload to `wb-action-box` (e.g., `{"action":"retry","retry_id":"..."}`) and the server handler `handle_action_json` shall dispatch to `scripts.world_builder.perform_retry` or `scripts.world_builder.open_folder` and return a toast or formatted error response.

#### Scenario: Confirmation modal
- Given an action that requires confirmation (e.g., Save New Version, Discard draft)
- When the user clicks Confirm
- Then the server SHALL perform the action and hide the modal; when user clicks Cancel the server SHALL hide the modal without performing the action.

## MODIFIED Requirements

#### Requirement: Tests and validation
- The system SHALL include unit tests for the new server-side handlers and smoke tests for `create_app()` mounting. E2E tests are recommended as follow-up.

## Notes
- UI visuals are guided by `stitch_world_editor_wireframe` HTML files. Implementations MAY approximate visuals with injected CSS; pixel-perfect accuracy is not required in this change.


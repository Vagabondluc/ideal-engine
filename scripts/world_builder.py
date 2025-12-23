import gradio as gr
import json
import os
import time
import shutil
from pathlib import Path
from src.utils import config as wb_config
from src.indexer import get_world_tree, get_world_files, get_world_latest_mtime
from src.runner import run_ollama_gen

# Minimal, safe stubs to allow iterative refactor and linting.
SHOW_ADVANCED_ERRORS = False
AUTOSAVE_ENABLED = True
CONFIG_PATH = Path('.world_builder_config.json')

# Editor & watcher state
EDITOR_IS_DIRTY = False
ORIGINAL_EDITOR_CONTENT = ''
CURRENT_EDITOR_PATH = ''

# World DB watch state
LAST_WORLD_MTIME = 0
DEBOUNCE_SECONDS = 1.5
LAST_DETECTED_AT = 0


def load_config():
    global SHOW_ADVANCED_ERRORS, AUTOSAVE_ENABLED
    try:
        cfg = wb_config.load_config(CONFIG_PATH)
        SHOW_ADVANCED_ERRORS = bool(cfg.get('SHOW_ADVANCED_ERRORS', SHOW_ADVANCED_ERRORS))
        AUTOSAVE_ENABLED = bool(cfg.get('AUTOSAVE_ENABLED', AUTOSAVE_ENABLED))
    except Exception:
        pass


def save_config():
    try:
        cfg = {'SHOW_ADVANCED_ERRORS': SHOW_ADVANCED_ERRORS, 'AUTOSAVE_ENABLED': AUTOSAVE_ENABLED}
        wb_config.save_config(CONFIG_PATH, cfg)
    except Exception:
        pass


def start_world_watcher():
    # Placeholder: real watcher moved to `src/watcher.py` during refactor.
    try:
        from src.watcher import start_world_watcher as _s
        return _s()
    except Exception:
        return None


# Small helpers ------------------------------------------------------------

def html_escape(s):
    if s is None:
        return ''
    return (str(s)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))


def format_error_enhanced(title, detail=None, suggestions=None, stderr=None, show_advanced=False, retry_id=None, folder_path=None):
    """Minimal, html-friendly error builder used by UI stubs.

    Keep this simple and safe so it can be used before the full UI is restored.
    """
    parts = []
    if detail:
        parts.append(f"<div style='margin-top:6px'>{html_escape(detail)}</div>")
    if suggestions:
        items = ''.join(f"<li>{html_escape(str(s))}</li>" for s in suggestions)
        parts.append(f"<div style='margin-top:8px'><strong>Try:</strong><ul style='margin:6px 0 0 18px'>{items}</ul></div>")

    diagnostic_block = ''
    if stderr and show_advanced:
        # include a small copy button so users can easily copy diagnostic details
        diagnostic_block = (
            f"<details style='margin-top:8px'><summary>Show full details</summary>"
            f"<pre style='white-space:pre-wrap;margin-top:8px;background:#f7f7f7;padding:8px;border-radius:6px'>{html_escape(stderr)}</pre>"
            f"<div style='margin-top:6px'><button data-copy-details='true'>Copy details</button></div></details>"
        )

    action_buttons = []
    if retry_id:
        action_buttons.append(f"<button data-retry-id='{html_escape(retry_id)}'>Retry</button>")
    if folder_path:
        # Ensure path is HTML-escaped; UI will handle click wiring to invoke open_folder safely
        action_buttons.append(f"<button data-open-folder='{html_escape(folder_path)}'>Open containing folder</button>")

    actions_html = ("<div style='margin-top:10px;'>" + " ".join(action_buttons) + "</div>") if action_buttons else ''
    # Keep existing buttons but annotate them with data attributes so client-side
    # JS can attach handlers without modifying markup elsewhere.
    # For example: <button data-retry-id='...'>Retry</button> or <button data-open-folder='...'>Open folder</button>

    return (
        f"<div class='wb-error-box' style='background:#fff2f0;border:1px solid #ffb3a7;color:#5b1414;padding:10px;border-radius:6px;'>"
        f"<strong>❌ {html_escape(title)}</strong>"
        f"{''.join(parts)}"
        f"{diagnostic_block}"
        f"{actions_html}"
        f"</div>"
    )


def get_activity_log_html(limit=200):
    try:
        p = Path('world_db') / '.activity.log'
        if not p.exists():
            return "<div style='color:#666'>No activity yet.</div>"
        with p.open('r', encoding='utf-8') as f:
            lines = [l.strip() for l in f if l.strip()]
        lines = list(reversed(lines))[:limit]
        items = ''.join(f"<li style='margin-bottom:6px'><code>{html_escape(l)}</code></li>" for l in lines)
        return f"<div style='max-height:260px;overflow:auto;padding:6px;background:#fafafa;border:1px solid #eee;border-radius:6px'><ul style='margin:0;padding-left:12px'>{items}</ul></div>"
    except Exception as e:
        return format_error_enhanced("Unable to read activity log", detail=str(e), suggestions=["Check file permissions on world_db/.activity.log"], stderr=str(e), show_advanced=SHOW_ADVANCED_ERRORS)


def log_activity(msg):
    try:
        p = Path('world_db') / '.activity.log'
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('a', encoding='utf-8') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")
    except Exception:
        pass


def refresh_tree():
    tree = get_world_tree()
    files = get_world_files()
    return tree, {'choices': files, 'value': (files[0] if files else None)}




def create_app():
    with gr.Blocks(title="World Builder — (stub)") as app:
        gr.Markdown("## World Builder — UI temporarily stubbed for refactor")
    return app


if __name__ == "__main__":
    load_config()
    try:
        Path('world_db').mkdir(parents=True, exist_ok=True)
        Path('world_db/.last_mod').write_text(str(time.time()))
    except Exception:
        pass

    start_world_watcher()

    try:
        LAST_WORLD_MTIME = get_world_latest_mtime()
    except Exception:
        LAST_WORLD_MTIME = 0

    app = create_app()
    app.launch(theme=gr.themes.Soft())

# NOTE: The original UI and many callback handlers were removed during the
# decomposition step to make the module importable and easier to refactor into
# smaller modules under `src/`. If you need pieces from the legacy UI, they are
# preserved in `scripts/world_builder_full_backup.py` for selective extraction.

def clear_activity(confirm=False):
    try:
        p = Path('world_db') / '.activity.log'
        if not p.exists():
            return get_activity_log_html()
        # Backup and clear
        bak = p.with_suffix('.log.bak')
        try:
            p.replace(bak)
        except Exception:
            # if replace fails, try rename
            import shutil
            shutil.copy2(p, bak)
            p.unlink()
        # Do not write a new activity entry after clearing; leave the log empty
        return get_activity_log_html()
    except Exception as e:
        return format_error_enhanced('Unable to clear log', detail=str(e), suggestions=['Check file permissions'], stderr=str(e), show_advanced=SHOW_ADVANCED_ERRORS)



# Database & Editor UI removed during decomposition. See `scripts/world_builder_full_backup.py` for original UI blocks.






            # Update the change wiring to include preview and prompt
# UI wiring removed during decomposition: `world_file_select_edit.change(...)`

            # -------------------------------
            # Editor: Save / Version / Revert
            # -------------------------------

def draft_path_for(relpath):
    safe_rel = relpath.replace('..', '').lstrip('/')
    return os.path.join('world_db', '.drafts', safe_rel + '.draft.md')

def persist_draft(relpath, content, force=False):
    try:
        if not AUTOSAVE_ENABLED and not force:
            return False
        dp = draft_path_for(relpath or f'unsaved_{int(time.time())}')
        os.makedirs(os.path.dirname(dp), exist_ok=True)
        with open(dp, 'w', encoding='utf-8') as f:
            f.write(content or '')
        try:
            log_activity(f"Draft saved: {relpath}")
        except Exception:
            pass
        return True
    except Exception:
        return False


def clear_draft(relpath):
    try:
        dp = draft_path_for(relpath)
        if os.path.exists(dp):
            os.remove(dp)
        return True
    except Exception:
        return False


def find_draft(relpath):
    dp = draft_path_for(relpath)
    if os.path.exists(dp):
        try:
            with open(dp, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return None
    return None


def on_editor_change(current_text):
    """Detect when editor content diverges from original and persist draft."""
    global EDITOR_IS_DIRTY, ORIGINAL_EDITOR_CONTENT, CURRENT_EDITOR_PATH
    # Persist draft on every change (lightweight) only if autosave enabled
    try:
        if CURRENT_EDITOR_PATH:
            persist_draft(CURRENT_EDITOR_PATH, current_text)
        else:
            # unsaved working buffer; store under unsaved timestamp
            persist_draft(f'unsaved_{int(time.time())}', current_text)
    except Exception:
        pass
    if current_text != ORIGINAL_EDITOR_CONTENT:
        EDITOR_IS_DIRTY = True
        ctx_html = f"<div style='background:#fff8dc;border-left:4px solid #ff8c00;padding:10px 14px;font-family:system-ui;'><strong>📌 Context:</strong> World Editor<br><strong>Path:</strong> {CURRENT_EDITOR_PATH or '(none)'}<br><strong>State:</strong> <span style='color:#ff8c00;'>⚠️ Modified (unsaved)</span></div>"
        warn_html = "<div style='background:#ffe4b5;border:1px solid #ff8c00;padding:8px;border-radius:6px;color:#8b4513;'>⚠️ You have unsaved changes. Save or Revert before switching entries.</div>"
        # Show restore button if draft exists
        draft_exists = bool(find_draft(CURRENT_EDITOR_PATH)) if CURRENT_EDITOR_PATH else False
        # update activity log preview
        activity_html = get_activity_log_html()
        return ctx_html, warn_html, gr.update(visible=draft_exists), activity_html
    else:
        EDITOR_IS_DIRTY = False
        ctx_html = f"<div style='background:#f0f0f0;border-left:4px solid #666;padding:10px 14px;font-family:system-ui;'><strong>📌 Context:</strong> World Editor<br><strong>Path:</strong> {CURRENT_EDITOR_PATH or '(none)'}<br><strong>State:</strong> <span style='color:green;'>✅ Clean</span></div>"
        activity_html = get_activity_log_html()
        return ctx_html, "", gr.update(visible=False), activity_html
def save_editor(relpath, content):
    if not relpath:
        return "No entry selected", content
    path = os.path.join('world_db', relpath)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content or '')
        try:
            Path('world_db/.last_mod').write_text(str(time.time()))
        except Exception:
            pass
        # Reset dirty state
        global EDITOR_IS_DIRTY, ORIGINAL_EDITOR_CONTENT
        EDITOR_IS_DIRTY = False
        ORIGINAL_EDITOR_CONTENT = content
        ctx_html = f"<div style='background:#f0f0f0;border-left:4px solid:#666;padding:10px 14px;font-family:system-ui;'><strong>📌 Context:</strong> World Editor<br><strong>Path:</strong> {relpath}<br><strong>State:</strong> <span style='color:green;'>✅ Clean (saved)</span></div>"
        tree_upd, files_upd = refresh_tree()
        try:
            log_activity(f"Saved {relpath}")
        except Exception:
            pass
        return f"<script>showWBToast('✅ Saved {html_escape(relpath)}','info');</script>", content, tree_upd, files_upd, ctx_html, "", get_activity_log_html()
    except Exception as e:
        return f"<script>showWBToast('❌ Error saving: {html_escape(str(e))}','error');</script>", content, "", "", "", "", get_activity_log_html()

            


# Legacy AI assist and related wiring removed during decomposition.
# Implement in `src/ui` when rebuilding the interface.

            # Confirmation modal click wiring (after components are defined)
# confirm_discard_btn wiring removed during decomposition
# confirm_save_draft_btn wiring removed during decomposition
# confirm_discard_draft_btn wiring removed during decomposition
# confirm_cancel_btn wiring removed during decomposition
# confirm_save_and_nav_btn wiring removed during decomposition
# restore_draft_btn wiring removed during decomposition
            # Wire JS-driven hidden boxes to handlers
# wb_retry_box wiring removed during decomposition
# wb_open_folder_box wiring removed during decomposition
# Activity log controls removed during decomposition

# Discard draft handler removed during decomposition
# refresh button wiring removed during decomposition



def check_for_updates(_=None):
    """Returns updates when world_db has changed (used by poll button).
    Implements debouncing: wait for DEBOUNCE_SECONDS of stability before refreshing.
    SUSPENDS auto-refresh when editor has unsaved changes to avoid overwriting user edits."""
    global LAST_WORLD_MTIME, LAST_DETECTED_AT, EDITOR_IS_DIRTY
    # Suspend auto-refresh if editor has unsaved changes
    if EDITOR_IS_DIRTY:
        return gr.update(), gr.update(), gr.update(), gr.update(), "⚠️ Auto-refresh suspended (unsaved changes in editor)", gr.update(), gr.update()

    latest = get_world_latest_mtime()
    # Also consider explicit marker file touches
    try:
        marker = Path('world_db/.last_mod')
        if marker.exists():
            m = float(marker.read_text() or 0)
            if m > latest:
                latest = m
    except Exception:
        pass

    # If a new change is observed, record detection time and wait for debounce window
    if latest > (LAST_WORLD_MTIME or 0):
        now = time.time()
        # If we haven't recorded a detection yet, start debouncing
        if LAST_DETECTED_AT == 0:
            LAST_DETECTED_AT = now
            return gr.update(), gr.update(), gr.update(), gr.update(), "⏳ Change detected — waiting for stability...", gr.update(), gr.update()
        else:
            # Update the detection timestamp to coalesce bursts
            LAST_DETECTED_AT = now
            # If enough time has passed since the first detection, perform refresh
            if (now - LAST_DETECTED_AT) >= DEBOUNCE_SECONDS:
                # Reset detection flag and perform update
                LAST_DETECTED_AT = 0
                LAST_WORLD_MTIME = latest
                tree = get_world_tree()
                files = get_world_files()
                tree_update = gr.update(value=tree)
                files_update = gr.update(choices=files, value=(files[0] if files else None))
                status_msg = f"✅ Auto-refreshed ({len(files)} files)"
                ts = time.strftime('%Y-%m-%d %H:%M:%S')
                toast_script = f"<script>showWBToast({json.dumps(status_msg)}, 'info');</script>"
                return tree_update, files_update, tree_update, files_update, ts, toast_script
            # Not yet stable
            return gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), "<script>showWBToast('⏳ Change detected — debouncing...','warn');</script>"

    def set_debounce(val):
        global DEBOUNCE_SECONDS
        try:
            DEBOUNCE_SECONDS = float(val)
            save_config()
            return f"<script>showWBToast('Debounce set to {DEBOUNCE_SECONDS:.1f}s','info');</script>"
        except Exception as e:
            return f"<script>showWBToast('Error setting debounce: {html_escape(str(e))}','error');</script>"

# ----- Actions: Retry & Open Folder -----

def perform_retry(retry_id: str):
    """Attempt to retry an operation recorded in RETRY_REGISTRY.

    Returns an HTML toast or error message for UI display.
    """
    try:
        from src.runner import RETRY_REGISTRY, run_ollama_gen
    except Exception:
        return "<script>showWBToast('Retry not available','error');</script>"
    if retry_id not in RETRY_REGISTRY:
        return "<script>showWBToast('Unknown retry id','error');</script>"
    entry = RETRY_REGISTRY.get(retry_id, {})
    op = entry.get('op')
    if op == 'ollama_run':
        prompt = entry.get('prompt')
        model = entry.get('model')
        temp = entry.get('temp')
        ok, payload = run_ollama_gen(prompt, model, temp, timeout=30)
        if ok:
            try:
                log_activity(f"Retry succeeded for {retry_id}")
            except Exception:
                pass
            return "<script>showWBToast('✅ Retry succeeded','info');</script>"
        else:
            detail = payload.get('detail') or payload.get('error')
            rid = payload.get('retry_id')
            return format_error_enhanced('Retry failed', detail=str(detail), retry_id=rid, show_advanced=SHOW_ADVANCED_ERRORS)
    return "<script>showWBToast('Unsupported retry op','error');</script>"


def open_folder(path: str):
    """Attempt to open a folder in the OS file browser. Returns (ok, message)."""
    try:
        if not path:
            return False, 'No path specified'
        p = Path(path)
        # Restrict to existing folders and workspace/world_db subtree for safety
        if not p.exists():
            return False, 'Path does not exist'
        allowed_roots = [Path('.').resolve(), Path('world_db').resolve()]
        resolved = p.resolve()
        if not any(str(resolved).startswith(str(r)) for r in allowed_roots):
            return False, 'Not allowed to open this path'
        try:
            # Windows: os.startfile, POSIX: use xdg-open or open
            if os.name == 'nt':
                os.startfile(str(resolved))
            else:
                import subprocess
                opener = 'xdg-open' if shutil.which('xdg-open') else 'open'
                subprocess.Popen([opener, str(resolved)])
            try:
                log_activity(f"Opened folder: {resolved}")
            except Exception:
                pass
            return True, f'Opened {resolved}'
        except Exception as e:
            return False, f'Failed to open: {e}'
    except Exception as e:
        return False, f'Error: {e}'


def set_debounce(val):
    """Set the debounce window for auto-refresh (module-level helper)."""
    global DEBOUNCE_SECONDS
    try:
        DEBOUNCE_SECONDS = float(val)
        save_config()
        return f"<script>showWBToast('Debounce set to {DEBOUNCE_SECONDS:.1f}s','info');</script>"
    except Exception as e:
        return f"<script>showWBToast('Error setting debounce: {html_escape(str(e))}','error');</script>"
    def set_debounce(val):
        global DEBOUNCE_SECONDS
        try:
            DEBOUNCE_SECONDS = float(val)
            save_config()
            return f"<script>showWBToast('Debounce set to {DEBOUNCE_SECONDS:.1f}s','info');</script>"
        except Exception as e:
            return f"<script>showWBToast('Error setting debounce: {html_escape(str(e))}','error');</script>"

    # debounce handler still registered to keep API consistent; actual component
    # will be added when rebuilding the UI in `src/ui`.



# ---------- Versioning & Revert Helpers ----------

def _versions_dir_for(relpath: str) -> str:
    safe_rel = relpath.replace('..', '').lstrip('/') if relpath else ''
    return os.path.join('world_db', '.versions', os.path.dirname(safe_rel), os.path.basename(safe_rel))


def list_versions(relpath: str) -> list:
    try:
        vd = _versions_dir_for(relpath)
        if not os.path.isdir(vd):
            return []
        files = sorted([f for f in os.listdir(vd) if f.lower().endswith('.md')])
        # return filenames without extension
        return [os.path.splitext(f)[0] for f in files]
    except Exception:
        return []


def save_new_version(relpath: str, content: str, notes: str | None = None):
    """Save a new immutable version and optional metadata (notes).

    Writes the version file under `.versions/.../v_{ts}.md` and a metadata JSON
    alongside it (`v_{ts}.meta.json`) containing notes and a timestamp.
    """
    if not relpath:
        return "No entry selected"
    try:
        vd = _versions_dir_for(relpath)
        os.makedirs(vd, exist_ok=True)
        ts = time.strftime('%Y%m%dT%H%M%S')
        fname = f"v_{ts}.md"
        outp = os.path.join(vd, fname)
        with open(outp, 'w', encoding='utf-8') as f:
            f.write(content or '')
        # write metadata
        meta = {'version': fname, 'timestamp': ts, 'notes': notes or ''}
        try:
            meta_path = outp + '.meta.json'
            with open(meta_path, 'w', encoding='utf-8') as mf:
                import json
                json.dump(meta, mf, indent=2, ensure_ascii=False)
        except Exception:
            pass
        try:
            log_activity(f"Saved version {relpath} -> {fname}")
        except Exception:
            pass
        return f"✅ Saved version {fname}"
    except Exception as e:
        return f"❌ Error saving version: {str(e)}"


def load_version(relpath: str, version_id: str):
    try:
        vd = _versions_dir_for(relpath)
        path = os.path.join(vd, version_id + '.md')
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None


def revert_editor(relpath: str):
    # Read canonical file and return its content and a status message
    try:
        path = os.path.join('world_db', relpath)
        if not os.path.exists(path):
            return "No entry found to revert", ''
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        global ORIGINAL_EDITOR_CONTENT, EDITOR_IS_DIRTY, CURRENT_EDITOR_PATH
        ORIGINAL_EDITOR_CONTENT = content
        EDITOR_IS_DIRTY = False
        CURRENT_EDITOR_PATH = relpath
        try:
            log_activity(f"Reverted {relpath}")
        except Exception:
            pass
        return f"Reverted {relpath}", content
    except Exception as e:
        return f"Error reverting: {str(e)}", ''


def restore_draft(relpath: str):
    try:
        draft = find_draft(relpath)
        if draft is None:
            return None
        try:
            log_activity(f"Restored draft for {relpath}")
        except Exception:
            pass
        return draft
    except Exception:
        return None


# ----------------
# AI Assist helper
# ----------------

def ai_assist_action(action: str, content: str, model: str, temp: float):
    """Perform a small AI-assist action and return (visible_update, suggestion, status)."""
    prompt_text = f"{action}\n\n{content}"
    try:
        res = run_ollama_gen(prompt_text, model, temp)
        # Support both (ok, payload) and simple string return for test stubs
        suggestion = ''
        if isinstance(res, tuple):
            ok, payload = res
            if ok:
                suggestion = payload.get('stdout', '') or payload.get('detail', '')
            else:
                suggestion = payload.get('error', '') or ''
        else:
            suggestion = str(res or '')
        return gr.update(visible=True), suggestion, '✅ Suggestion ready'
    except Exception as e:
        return gr.update(visible=True), format_error_enhanced('AI assist failed', detail=str(e), show_advanced=SHOW_ADVANCED_ERRORS), '❌ Error'

# -------------------------------------------------------------
# LAUNCH
# -------------------------------------------------------------
if __name__ == "__main__":
    # Initialize watcher thread then launch app
    try:
        # Ensure world_db exists
        Path('world_db').mkdir(parents=True, exist_ok=True)
        # Seed initial marker
        Path('world_db/.last_mod').write_text(str(time.time()))
    except Exception:
        pass

    # Start watchdog watcher in background (no-op if watchdog not installed)
    start_world_watcher()

    # Set initial LAST_WORLD_MTIME
    try:
        LAST_WORLD_MTIME = get_world_latest_mtime()
    except Exception:
        LAST_WORLD_MTIME = 0

    app = create_app()

    app.launch(theme=gr.themes.Soft())

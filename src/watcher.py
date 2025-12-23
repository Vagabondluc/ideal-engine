"""Filesystem watcher utilities (optional dependency on watchdog)."""
import os
import time
import sys
from pathlib import Path
from . import indexer

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except Exception:
    WATCHDOG_AVAILABLE = False

# --- World DB Watcher (for UI refresh) ---

class _WorldEventHandler(FileSystemEventHandler if WATCHDOG_AVAILABLE else object):
    def on_any_event(self, event):
        try:
            Path('world_db/.last_mod').write_text(str(time.time()))
        except Exception:
            pass

def start_world_watcher():
    if not WATCHDOG_AVAILABLE:
        return None
    root = Path('world_db')
    if not root.exists():
        return None
    observer = Observer()
    handler = _WorldEventHandler()
    observer.schedule(handler, str(root), recursive=True)
    observer.daemon = True
    observer.start()
    return observer

# --- Narrative Scripts Watcher (from scripts/watcher.py) ---

class IndexRebuildHandler(FileSystemEventHandler if WATCHDOG_AVAILABLE else object):
    def __init__(self, scripts_root: str):
        super().__init__()
        self.scripts_root = scripts_root

    def on_any_event(self, event):
        try:
            idx = indexer.generate_index(self.scripts_root)
            indexer.write_index(idx, os.path.join(self.scripts_root, 'index.json'))
            print('Rebuilt index.json')
        except Exception as e:
            print('Watcher error:', e)

def run_watcher(scripts_root='scripts'):
    if not WATCHDOG_AVAILABLE:
        print("Watchdog not available.")
        return
    paths = [
        os.path.join(scripts_root, 'canonical'),
        os.path.join(scripts_root, 'versions'),
    ]
    observer = Observer()
    handler = IndexRebuildHandler(scripts_root)
    for p in paths:
        if os.path.isdir(p):
            observer.schedule(handler, p, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_watcher(sys.argv[1])
    else:
        print('watcher OK')

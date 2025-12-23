import os
import json
from pathlib import Path
from typing import List, Dict, Any

"""Indexing and world-db file helpers.

Functions:
- load_index(path=...)
- get_world_tree(root='world_db')
- get_world_files(root='world_db')
- get_world_latest_mtime(root='world_db')
- generate_index(scripts_root=...)
- write_index(index, out_path)
- add_version(scripts_root, category, script_name, content, notes)
"""

INDEX_PATH_DEFAULT = 'narrative_scripts_index.json'

def load_index(path: str = INDEX_PATH_DEFAULT) -> Dict:
    p = Path(path)
    if not p.exists():
        return {"scripts": []}
    try:
        with p.open('r', encoding='utf-8') as fh:
            return json.load(fh)
    except Exception:
        return {"scripts": []}

def get_world_tree(root: str = 'world_db') -> str:
    world_root = Path(root)
    if not world_root.exists():
        return f"{root}/ not found"
    lines = []
    for r, dirs, files in os.walk(world_root):
        try:
            level = Path(r).relative_to(world_root).parts
            indent = '  ' * len(level)
            lines.append(f"{indent}{Path(r).name}/")
            subindent = '  ' * (len(level) + 1)
            for fn in files:
                lines.append(f"{subindent}{fn}")
        except Exception:
            continue
    return '\n'.join(lines) if lines else f"{root}/ is empty"

def get_world_files(root: str = 'world_db') -> List[str]:
    root_p = Path(root)
    files = []
    if not root_p.exists():
        return files
    for dirpath, dirnames, filenames in os.walk(root_p):
        for fn in filenames:
            if fn.lower().endswith('.md'):
                rel = os.path.relpath(os.path.join(dirpath, fn), start=str(root_p))
                files.append(rel.replace('\\', '/'))
    return sorted(files)

def get_world_latest_mtime(root: str = 'world_db') -> float:
    root_p = Path(root)
    latest = 0.0
    if not root_p.exists():
        return latest
    for dirpath, dirnames, filenames in os.walk(root_p):
        for fn in filenames:
            path = os.path.join(dirpath, fn)
            try:
                m = os.path.getmtime(path)
            except Exception:
                m = 0
            if m > latest:
                latest = m
    return latest

# --- Narrative Scripts Indexing (from scripts/indexer.py) ---

def generate_index(scripts_root: str) -> Dict[str, Any]:
    """Generate an index dictionary for the scripts storage layout.
    Scans all .txt files recursively under scripts_root.
    """
    result = {"scripts": []}
    if not os.path.isdir(scripts_root):
        return result

    canonical_dir = os.path.join(scripts_root, "canonical")
    if os.path.isdir(canonical_dir):
        scan_root = canonical_dir
        versions_dir = os.path.join(scripts_root, "versions")
    else:
        scan_root = scripts_root
        versions_dir = os.path.join(scripts_root, "versions")

    for root, _, files in os.walk(scan_root):
        for fname in files:
            if not fname.lower().endswith('.txt'):
                continue
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, scan_root)
            parts = rel_path.replace('\\', '/').split('/')
            
            if len(parts) < 2:
                category = "Misc"
                script_name = parts[0].rsplit('.', 1)[0]
            else:
                category = parts[0]
                script_name = '/'.join(parts[1:]).rsplit('.', 1)[0]

            versions_list = []
            version_path = os.path.join(versions_dir, category, script_name)
            if os.path.isdir(version_path):
                for v in sorted(os.listdir(version_path)):
                    if v.lower().endswith('.txt'):
                        versions_list.append(v.rsplit('.', 1)[0])

            item = {
                "id": f"{category}/{script_name}",
                "category": category,
                "canonical_path": full_path,
                "versions": versions_list,
                "meta": {}
            }
            result["scripts"].append(item)
    return result

def write_index(index: Dict[str, Any], out_path: str) -> None:
    dirname = os.path.dirname(out_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

def add_version(scripts_root: str, category: str, script_name: str, content: str, notes: str | None = None) -> str:
    versions_dir = os.path.join(scripts_root, 'versions', category, script_name)
    os.makedirs(versions_dir, exist_ok=True)

    existing = [f for f in os.listdir(versions_dir) if f.lower().endswith('.txt')]
    nums = []
    for e in existing:
        try:
            if e.startswith('v'):
                nums.append(int(e[1:].split('.', 1)[0]))
        except Exception:
            continue
    next_num = max(nums) + 1 if nums else 1
    fname = f'v{next_num}.txt'
    out_path = os.path.join(versions_dir, fname)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(content)

    meta = {'version': f'v{next_num}', 'notes': notes or ''}
    meta_path = os.path.join(versions_dir, 'meta.json')
    try:
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as mf:
                old = json.load(mf)
        else:
            old = {'versions': []}
        old['versions'].append(meta)
        with open(meta_path, 'w', encoding='utf-8') as mf:
            json.dump(old, mf, indent=2, ensure_ascii=False)
    except Exception:
        pass

    idx = generate_index(scripts_root)
    write_index(idx, os.path.join(scripts_root, 'index.json'))
    return out_path

if __name__ == "__main__":
    print('indexer OK')

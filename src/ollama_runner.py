#!/usr/bin/env python3
"""Ollama runner: choose a model and a prompt file from Narrative Scripts and run it.

Usage examples:
  python src/ollama_runner.py --list-prompts
  python src/ollama_runner.py --model llama2 --prompt "Narrative Scripts/bring_ur_outline.md"
  python src/ollama_runner.py --endpoint http://localhost:11434 --model llama2 --prompt "Narrative Scripts/bring_ur_outline.md"

Notes:
- By default the script prefers the Ollama CLI (if present). If `--endpoint` is given, it will POST JSON {model, prompt} to that endpoint.
- The exact HTTP API schema depends on the user's Ollama HTTP server. This script uses a conservative JSON shape and will print the raw response.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import shutil
from typing import Optional


NARRATIVE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Narrative Scripts")
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache")
MODEL_CACHE_FILE = os.path.join(CACHE_DIR, "ollama_models.json")


def list_prompts() -> list[str]:
    # Legacy: flat list of files at top level
    if not os.path.isdir(NARRATIVE_DIR):
        return []
    files = [f for f in os.listdir(NARRATIVE_DIR) if os.path.isfile(os.path.join(NARRATIVE_DIR, f))]
    files.sort()
    return files


def walk_prompt_tree() -> dict:
    """Return a nested dict representing the directory tree under NARRATIVE_DIR.

    Keys are names; values are either dict (subdirectory) or None for files.
    """
    tree: dict = {}
    if not os.path.isdir(NARRATIVE_DIR):
        return tree
    for root, dirs, files in os.walk(NARRATIVE_DIR):
        rel_root = os.path.relpath(root, NARRATIVE_DIR)
        node = tree
        if rel_root != ".":
            for part in rel_root.split(os.sep):
                node = node.setdefault(part, {})
        for d in sorted(dirs):
            node.setdefault(d, {})
        for f in sorted(files):
            node[f] = None
    return tree


def choose_prompt_interactive() -> Optional[str]:
    # Interactive navigator that reflects the folder hierarchy under NARRATIVE_DIR.
    if not os.path.isdir(NARRATIVE_DIR):
        print(f"No prompt directory found at '{NARRATIVE_DIR}'", file=sys.stderr)
        return None

    cur_path = NARRATIVE_DIR
    while True:
        try:
            entries = sorted(os.listdir(cur_path))
        except Exception as e:
            print(f"Failed to list directory: {e}", file=sys.stderr)
            return None

        dirs = [e for e in entries if os.path.isdir(os.path.join(cur_path, e))]
        files = [e for e in entries if os.path.isfile(os.path.join(cur_path, e))]

        print(f"\nCurrent: {os.path.relpath(cur_path, NARRATIVE_DIR)}")
        idx = 1
        index_map: dict[int, tuple[str, str]] = {}
        for d in dirs:
            print(f"{idx}) [DIR]  {d}")
            index_map[idx] = ("dir", d)
            idx += 1
        for f in files:
            print(f"{idx}) [FILE] {f}")
            index_map[idx] = ("file", f)
            idx += 1

        print("0) .. (go up)")
        print("q) cancel")
        sel = input("Choose an entry: ").strip()
        if sel.lower() == "q":
            print("Selection cancelled", file=sys.stderr)
            return None
        if sel == "0":
            if os.path.abspath(cur_path) == os.path.abspath(NARRATIVE_DIR):
                print("Already at top level")
                continue
            cur_path = os.path.dirname(cur_path)
            continue
        try:
            n = int(sel)
        except (ValueError, TypeError):
            print("Invalid selection", file=sys.stderr)
            continue
        if n not in index_map:
            print("Invalid selection", file=sys.stderr)
            continue
        kind, name = index_map[n]
        selected = os.path.join(cur_path, name)
        if kind == "dir":
            cur_path = selected
            continue
        else:
            return selected


def interactive_config_menu() -> dict:
    """Interactive menu to configure client, host/endpoint, model, and prompt.

    Returns a dict with keys: client, endpoint, host, model, prompt
    """
    config: dict = {"client": None, "endpoint": None, "host": None, "model": None, "prompt": None}

    # Choose client
    available_clients = ["cli", "python", "http"]
    default_client = None
    if shutil.which('ollama'):
        default_client = 'cli'
    else:
        import importlib.util
        if importlib.util.find_spec('ollama') is not None:
            default_client = 'python'
        else:
            default_client = 'http'    

    print("Select backend client:")
    for i, c in enumerate(available_clients, start=1):
        default_mark = ' (default)' if c == default_client else ''
        print(f"{i}) {c}{default_mark}")
    sel = input(f"Choose client [default {default_client}]: ").strip()
    if not sel:
        config['client'] = default_client
    else:
        if sel.isdigit():
            idx = int(sel) - 1
            if 0 <= idx < len(available_clients):
                config['client'] = available_clients[idx]
            else:
                print("Invalid selection, using default", file=sys.stderr)
                config['client'] = default_client
        else:
            if sel in available_clients:
                config['client'] = sel
            else:
                print("Invalid selection, using default", file=sys.stderr)
                config['client'] = default_client

    # Ask for endpoint/host when needed
    if config['client'] == 'http':
        ep = input('HTTP endpoint (e.g. http://localhost:11434): ').strip()
        config['endpoint'] = ep or None
    if config['client'] == 'python':
        host = input('Python client host (leave empty for default local): ').strip()
        config['host'] = host or None

    # Choose model
    models: list[str] = []
    if config['client'] == 'cli' and shutil.which('ollama'):
        models = list_models_cli()
    elif config['client'] == 'python':
        try:
            import ollama  # type: ignore
            # Attempt to call module-level list() if available
            try:
                raw = ollama.list()  # type: ignore
                # Normalize various return shapes into a list
                def normalize_models_return(raw_val):
                    if raw_val is None:
                        return []
                    if isinstance(raw_val, (list, tuple)):
                        return list(raw_val)
                    if isinstance(raw_val, dict):
                        for key in ("models", "results", "data"):
                            if key in raw_val and isinstance(raw_val[key], (list, tuple)):
                                return list(raw_val[key])
                        return list(raw_val.keys())
                    if hasattr(raw_val, 'models'):
                        attr = getattr(raw_val, 'models')
                        if isinstance(attr, (list, tuple)):
                            return list(attr)
                    try:
                        lst = list(raw_val)
                        if len(lst) == 1 and isinstance(lst[0], tuple) and isinstance(lst[0][1], (list, tuple)):
                            return list(lst[0][1])
                        return lst
                    except Exception:
                        return [raw_val]

                models = normalize_models_return(raw)
            except Exception:
                models = load_models_from_cache()
        except Exception:
            models = load_models_from_cache()
    else:
        models = load_models_from_cache()

    if models:
        # normalize model entries to strings
        norm_models = []
        for m in models:
            name = extract_model_name(m)
            if name:
                norm_models.append(name)
        # dedupe while preserving order
        seen = set()
        uniq = []
        for m in norm_models:
            if m not in seen:
                seen.add(m)
                uniq.append(m)

        print("Available models:")
        for i, m in enumerate(uniq, start=1):
            print(f"{i}) {m}")
        sel = input('Choose a model by number or type a name: ').strip()
        if sel.isdigit():
            idx = int(sel) - 1
            if 0 <= idx < len(uniq):
                config['model'] = uniq[idx]
            else:
                print('Invalid selection', file=sys.stderr)
        else:
            config['model'] = sel or None
    else:
        m = input('Model name to use: ').strip()
        config['model'] = m or None

    # Choose prompt
    print('\nSelect prompt file:')
    prompt_path = choose_prompt_interactive()
    config['prompt'] = prompt_path

    return config


def read_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def call_ollama_cli(model: str, prompt: str) -> tuple[int, str, str]:
    """Attempt to run Ollama CLI. Returns (exitcode, stdout, stderr)."""
    ollama_path = shutil.which("ollama")
    if not ollama_path:
        return (2, "", "ollama binary not found")

    # We'll try to call `ollama run <model>` and feed prompt via stdin.
    # If the user's Ollama version uses different command names, they'll get stderr and can use --endpoint instead.
    cmd = [ollama_path, "run", model]
    try:
        proc = subprocess.run(cmd, input=prompt.encode("utf-8"), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        stdout = proc.stdout.decode("utf-8", errors="replace")
        stderr = proc.stderr.decode("utf-8", errors="replace")
        return (proc.returncode, stdout, stderr)
    except Exception as e:
        return (1, "", str(e))


def get_model_cache_path() -> str:
    return MODEL_CACHE_FILE


def list_models_cli() -> list[str]:
    """Call `ollama list` and return a list of model names. Also update cache file."""
    ollama_path = shutil.which("ollama")
    if not ollama_path:
        return []
    try:
        proc = subprocess.run([ollama_path, "list"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        out = proc.stdout.decode("utf-8", errors="replace")
        models: list[str] = []
        for line in out.splitlines():
            s = line.strip()
            if not s:
                continue
            # Skip header lines
            if s.lower().startswith("name") or s.lower().startswith("image"):
                continue
            # Take first token as model name
            parts = s.split()
            if parts:
                models.append(parts[0])

        # Persist cache
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(get_model_cache_path(), "w", encoding="utf-8") as f:
                json.dump({"models": models}, f, indent=2)
        except Exception:
            pass

        # dedupe while preserving order
        seen = set()
        uniq = []
        for m in models:
            if m not in seen:
                seen.add(m)
                uniq.append(m)
        return uniq
    except Exception:
        return []


def load_models_from_cache() -> list[str]:
    try:
        with open(get_model_cache_path(), "r", encoding="utf-8") as f:
            j = json.load(f)
            return j.get("models", [])
    except Exception:
        return []


def extract_model_name(item) -> str:
    """Extract a usable model name from various possible return types from Ollama list/show.

    Handles: str, dict, objects with attributes, or reprs.
    """
    if item is None:
        return ""
    # strings
    if isinstance(item, str):
        return item
    # dicts
    if isinstance(item, dict):
        for key in ("model", "name", "id", "tag"):
            if key in item and item[key]:
                return str(item[key])
        # try nested
        if "models" in item and isinstance(item["models"], (list, tuple)):
            # not a single model
            return ""
    # objects: try attributes
    for attr in ("model", "name", "id", "tag"):
        if hasattr(item, attr):
            try:
                val = getattr(item, attr)
                if val:
                    return str(val)
            except Exception:
                pass
    # Fallback to string and try to parse common repr patterns
    s = str(item)
    # try to find "model='NAME'" or "model=NAME"
    import re

    m = re.search(r"model\s*=\s*'([^']+)'", s)
    if not m:
        m = re.search(r"model\s*=\s*([\w\-:\@\.]+)", s)
    if m:
        return m.group(1)
    # last resort: return full string
    return s


def call_ollama_http(endpoint: str, model: str, prompt: str) -> tuple[int, str]:
    try:
        import requests
    except Exception:
        return (3, "requests package required for HTTP endpoint usage (pip install requests)")
    payload = {"model": model, "prompt": prompt}
    try:
        # Use streaming POST to handle chunked or long-running responses from Ollama HTTP API.
        # Use a longer read timeout to accommodate model generation time.
        r = requests.post(endpoint, json=payload, stream=True, timeout=(10, 300))
        status = r.status_code
        # If server returns SSE or chunked text, iterate and accumulate
        try:
            if r.headers.get("content-type", "").startswith("text/event-stream") or r.headers.get("transfer-encoding", "") == "chunked":
                parts = []
                for chunk in r.iter_content(chunk_size=None):
                    if not chunk:
                        continue
                    try:
                        parts.append(chunk.decode("utf-8", errors="replace"))
                    except Exception:
                        parts.append(str(chunk))
                return (status, "".join(parts))
            # Fallback: try to read text normally
            text = r.text
            return (status, text)
        except Exception:
            try:
                return (status, r.content.decode("utf-8", errors="replace"))
            except Exception as e:
                return (status, str(e))
    except Exception as e:
        return (1, str(e))


def call_ollama_python(model: str, prompt: str, stream: bool = False, host: Optional[str] = None, headers: Optional[dict] = None) -> tuple[int, str]:
    """Use the Ollama Python client to generate text. Returns (status, output).
    status 0 -> success, 1 -> runtime error, 3 -> missing dependency
    """
    try:
        from ollama import Client
    except Exception:
        return (3, "ollama Python package not installed; pip install ollama")

    try:
        client_kwargs = {}
        if host:
            client_kwargs['host'] = host
        if headers:
            client_kwargs['headers'] = headers
        client = Client(**client_kwargs) if client_kwargs else Client()
        # Use generate for prompt strings
        if stream:
            # stream is an iterator/generator
            parts = []
            for part in client.generate(model=model, prompt=prompt, stream=True):
                # part may be mapping or ChatResponse-like
                try:
                    content = part['message']['content']
                except Exception:
                    content = str(part)
                parts.append(content)
            return (0, ''.join(parts))
        else:
            resp = client.generate(model=model, prompt=prompt)
            try:
                # resp may be dict-like
                content = resp['message']['content']
            except Exception:
                # fallback to string
                content = str(resp)
            return (0, content)
    except Exception as e:
        return (1, str(e))


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    p = argparse.ArgumentParser(description="Run a prompt with an Ollama model")
    p.add_argument("--model", "-m", help="Model name to use")
    p.add_argument("--prompt", "-p", help="Path to prompt file (or name under Narrative Scripts)")
    p.add_argument("--list-models", action="store_true", help="List models via Ollama CLI (if available)")
    p.add_argument("--list-prompts", action="store_true", help="List prompt files under Narrative Scripts/")
    p.add_argument("--endpoint", help="HTTP endpoint to send JSON {model,prompt} to (fallback to CLI if omitted)")
    p.add_argument("--client", choices=["cli", "python", "http"], default=None, help="Which backend to use: 'cli' uses ollama CLI, 'python' uses ollama Python package, 'http' uses HTTP endpoint")
    p.add_argument("--host", help="Host to pass to Python Ollama Client (e.g., http://localhost:11434)")
    p.add_argument("--out-file", help="Write model output to this file")
    args = p.parse_args(argv)

    # If no CLI flags provided, run interactive configuration menu to populate args
    if not argv:
        cfg = interactive_config_menu()
        # populate namespace
        args.client = cfg.get('client')
        args.endpoint = cfg.get('endpoint')
        args.host = cfg.get('host')
        args.model = cfg.get('model')
        # allow prompt to be a path
        args.prompt = cfg.get('prompt')

    if args.list_prompts:
        prompts = list_prompts()
        if not prompts:
            print(f"No prompt files found in '{NARRATIVE_DIR}'", file=sys.stderr)
            return 0
        for name in prompts:
            print(name)
        return 0

    if args.list_models:
        ollama_path = shutil.which("ollama")
        if not ollama_path:
            print("ollama binary not found; cannot list models", file=sys.stderr)
            return 2
        try:
            proc = subprocess.run([ollama_path, "list"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            sys.stdout.write(proc.stdout.decode("utf-8", errors="replace"))
            sys.stderr.write(proc.stderr.decode("utf-8", errors="replace"))
            return proc.returncode
        except Exception as e:
            print(str(e), file=sys.stderr)
            return 1

    prompt_path = None
    if args.prompt:
        # Allow bare filenames relative to Narrative Scripts
        if os.path.isabs(args.prompt) and os.path.isfile(args.prompt):
            prompt_path = args.prompt
        else:
            candidate = os.path.join(NARRATIVE_DIR, args.prompt)
            if os.path.isfile(candidate):
                prompt_path = candidate
            elif os.path.isfile(args.prompt):
                prompt_path = args.prompt
            else:
                print(f"Prompt file not found: {args.prompt}", file=sys.stderr)
                return 2
    else:
        prompt_path = choose_prompt_interactive()
        if not prompt_path:
            return 2

    try:
        prompt_text = read_prompt(prompt_path)
    except Exception as e:
        print(f"Failed to read prompt: {e}", file=sys.stderr)
        return 2

    if not args.model:
        # If model not provided, attempt to list models (CLI) or from cache and prompt user to choose
        models = []
        if shutil.which("ollama"):
            models = list_models_cli()
        if not models:
            models = load_models_from_cache()

        if models:
            print("Available models:")
            for i, m in enumerate(models, start=1):
                print(f"{i}) {m}")
            try:
                sel = input("Choose a model by number (or type a model name): ").strip()
                if sel.isdigit():
                    idx = int(sel) - 1
                    if 0 <= idx < len(models):
                        args.model = models[idx]
                    else:
                        print("Invalid selection", file=sys.stderr)
                        return 2
                else:
                    args.model = sel
                if not args.model:
                    print("No model provided", file=sys.stderr)
                    return 2
            except (EOFError, KeyboardInterrupt):
                print("Selection cancelled", file=sys.stderr)
                return 2
        else:
            args.model = input("Model name to use: ").strip()
            if not args.model:
                print("No model provided", file=sys.stderr)
                return 2

    # Determine client backend
    chosen_client = args.client
    if chosen_client is None:
        if args.endpoint:
            chosen_client = 'http'
        else:
            # default to CLI if available, otherwise try python client, otherwise http
            if shutil.which('ollama'):
                chosen_client = 'cli'
            else:
                # check python package without importing the module (avoid binding unused name)
                import importlib.util
                if importlib.util.find_spec('ollama') is not None:
                    chosen_client = 'python'
                else:
                    chosen_client = 'cli'    

    if chosen_client == 'http':
        if not args.endpoint:
            print('HTTP client requested but no --endpoint provided', file=sys.stderr)
            return 2
        code, out = call_ollama_http(args.endpoint, args.model, prompt_text)
        if code == 0 or (100 <= code < 600):
            print(out)
            if args.out_file:
                with open(args.out_file, 'w', encoding='utf-8') as f:
                    f.write(out)
            return 0 if code < 400 else 1
        else:
            print(out, file=sys.stderr)
            return 1

    if chosen_client == 'python':
        host = args.host or None
        code, out = call_ollama_python(args.model, prompt_text, stream=False, host=host)
        if code == 3:
            print(out, file=sys.stderr)
            return 2
        if code == 0:
            print(out)
            if args.out_file:
                with open(args.out_file, 'w', encoding='utf-8') as f:
                    f.write(out)
            return 0
        else:
            print(out, file=sys.stderr)
            return 1

    # Otherwise use CLI
    exitcode, stdout, stderr = call_ollama_cli(args.model, prompt_text)

    # Otherwise use CLI
    exitcode, stdout, stderr = call_ollama_cli(args.model, prompt_text)
    if exitcode == 2:
        print("ollama binary not found; either install Ollama or provide --endpoint", file=sys.stderr)
        return 2
    if stdout:
        print(stdout)
        if args.out_file:
            with open(args.out_file, "w", encoding="utf-8") as f:
                f.write(stdout)
        return 0 if exitcode == 0 else 1
    else:
        print(stderr, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


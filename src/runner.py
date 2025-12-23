"""Runner for model execution (e.g., Ollama CLI).

This module provides a small, testable wrapper around subprocess calls and
returns structured results rather than embedding UI-specific HTML.
"""
from typing import Dict, Any, Tuple
import subprocess
import uuid

RETRY_REGISTRY: Dict[str, Dict[str, Any]] = {}


def run_ollama_gen(prompt_text: str, model: str, temp: float, timeout: int = 120) -> Tuple[bool, Dict[str, Any]]:
    """Run an Ollama model and return (success, payload).

    On success: (True, {'stdout': <text>})
    On failure: (False, {'error': <message>, 'stderr': <stderr>, 'retry_id': <id>})
    """
    if not prompt_text or not str(prompt_text).strip():
        return False, {'error': 'Prompt empty', 'suggestions': ['Provide a prompt']}
    try:
        result = subprocess.run(
            ['ollama', 'run', model, prompt_text],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout,
        )
        if result.returncode == 0:
            return True, {'stdout': result.stdout}
        else:
            detail = result.stderr.strip() or 'Unknown error from Ollama.'
            rid = str(uuid.uuid4())
            RETRY_REGISTRY[rid] = {'op': 'ollama_run', 'prompt': prompt_text, 'model': model, 'temp': temp}
            return False, {'error': 'Model execution failed', 'detail': detail, 'stderr': result.stderr, 'retry_id': rid}
    except FileNotFoundError:
        return False, {'error': 'Ollama not found', 'detail': 'Ollama CLI is not on PATH', 'suggestions': ['Install Ollama']}
    except subprocess.TimeoutExpired:
        rid = str(uuid.uuid4())
        RETRY_REGISTRY[rid] = {'op': 'ollama_run', 'prompt': prompt_text, 'model': model, 'temp': temp}
        return False, {'error': 'Model timeout', 'detail': 'Timed out', 'retry_id': rid}
    except Exception as e:
        rid = str(uuid.uuid4())
        RETRY_REGISTRY[rid] = {'op': 'ollama_run', 'prompt': prompt_text, 'model': model, 'temp': temp}
        return False, {'error': 'Model error', 'detail': str(e), 'retry_id': rid}


if __name__ == "__main__":
    print('runner OK')

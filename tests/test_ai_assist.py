import importlib.util
import os

spec = importlib.util.spec_from_file_location('world_builder', os.path.join(os.getcwd(), 'scripts', 'world_builder.py'))
wb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wb)


def test_ai_assist_stub(monkeypatch):
    # Stub run_ollama_gen to return modified content
    def fake_run(prompt_text, model, temp):
        return '## Modified\nModified content'

    monkeypatch.setattr(wb, 'run_ollama_gen', fake_run)

    visible_update, suggestion, status = wb.ai_assist_action('Shorten', '# Title\nSome long content', 'mistral:latest', 0.7)

    # Validate suggestion content
    assert suggestion.startswith('##'), 'AI suggestion not returned'
    assert 'Modified' in suggestion
    assert status == '✅ Suggestion ready'

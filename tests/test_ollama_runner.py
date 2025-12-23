import os
import unittest
from unittest import mock

import scripts.ollama_runner as runner


class TestOllamaRunner(unittest.TestCase):
    def test_list_prompts_empty(self):
        # Temporarily point NARRATIVE_DIR to a temp dir
        with mock.patch.object(runner, 'NARRATIVE_DIR', os.path.join(os.path.dirname(__file__), 'empty_narratives')):
            if not os.path.isdir(runner.NARRATIVE_DIR):
                os.makedirs(runner.NARRATIVE_DIR, exist_ok=True)
            prompts = runner.list_prompts()
            self.assertEqual(prompts, [])

    def test_call_ollama_cli_missing(self):
        with mock.patch('shutil.which', return_value=None):
            code, out, err = runner.call_ollama_cli('some-model', 'hi')
            self.assertEqual(code, 2)
            self.assertIn('not found', err.lower())

    def test_call_ollama_http_no_requests(self):
        # Simulate missing requests package by altering sys.modules
        with mock.patch.dict('sys.modules', {'requests': None}):
            code, out = runner.call_ollama_http('http://localhost:11434', 'm', 'p')
            self.assertEqual(code, 3)
            self.assertIn('requests', out)

    def test_call_ollama_python_missing(self):
        # Simulate missing ollama package
        with mock.patch.dict('sys.modules', {'ollama': None}):
            code, out = runner.call_ollama_python('m', 'p')
            self.assertEqual(code, 3)
            self.assertIn('pip install ollama', out)


if __name__ == '__main__':
    unittest.main()

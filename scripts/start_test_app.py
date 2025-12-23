import os
import time
from threading import Thread

# This script starts the Gradio app on port 7870 for E2E tests. It runs in
# the background thread so tests can connect to it. Use responsibly.

def start_app():
    try:
        os.environ['GRADIO_SERVER_PORT'] = '7870'
        # Ensure sample data exists for E2E tests
        os.makedirs('world_db', exist_ok=True)
        sample_path = os.path.join('world_db', 'e2e_sample.md')
        if not os.path.exists(sample_path):
            with open(sample_path, 'w', encoding='utf-8') as f:
                f.write('# E2E Sample\nLine one\nLine two\nLine three\n')
        from src.ui import create_app
        app = create_app()
        # Use a non-blocking launch for local E2E runs
        app.launch(server_name='127.0.0.1', server_port=7870, share=False)
    except Exception as e:
        print('Error launching test app:', e)

if __name__ == '__main__':
    t = Thread(target=start_app, daemon=True)
    t.start()
    print('Test app started in background (pid thread). Waiting for readiness...')
    time.sleep(2)
    print('Ready')

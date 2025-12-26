const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.E2E_PORT || '7871';
const HOST = '127.0.0.1';
const BASE_URL = `http://${HOST}:${PORT}`;
const PID_FILE = path.join(__dirname, '.server-pid');

function waitForServer(url, timeoutMs = 120000) {
  const start = Date.now();
  return new Promise((resolve, reject) => {
    (function check() {
      http.get(url, (res) => {
        // succeed on any response code
        resolve(true);
      }).on('error', (e) => {
        if (Date.now() - start > timeoutMs) return reject(new Error('Timeout waiting for server'));
        setTimeout(check, 200);
      });
    })();
  });
}

module.exports = async () => {
  // If a server is already running, reuse it
  try {
    await waitForServer(BASE_URL, 2000);
    // write sentinel pid 0 to indicate existing server
    fs.writeFileSync(PID_FILE, '0', 'utf8');
    console.log('Global setup: found existing server at', BASE_URL);
    return;
  } catch (e) {
    // continue to spawn
  }

  // Spawn Python process to run the app with handshake enabled
  const python = process.env.PYTHON || 'python';
  const code = `from src.world_builder import load_config; load_config(); from src.ui import create_app; app = create_app(); app.launch(server_name='${HOST}', server_port=${PORT}, share=False, debug=False)`;
  const env = Object.assign({}, process.env, { WB_E2E_HANDSHAKE: (process.env.WB_E2E_HANDSHAKE || '1'), E2E_BASE_URL: BASE_URL, PYTHONUNBUFFERED: '1' });

  console.log('Global setup: starting server:', python, ['-u', '-c', code].join(' '));
  const cwd = path.join(__dirname, '..', '..');
  const child = spawn(python, ['-u', '-c', code], { env, stdio: ['ignore', 'pipe', 'pipe'], detached: true, cwd });

  child.stdout && child.stdout.on('data', (d) => process.stdout.write(`[server stdout] ${d}`));
  child.stderr && child.stderr.on('data', (d) => process.stderr.write(`[server stderr] ${d}`));

  // Detach so it keeps running after this script exits; persist pid so teardown can kill it
  try {
    fs.writeFileSync(PID_FILE, String(child.pid), 'utf8');
    child.unref && child.unref();
  } catch (e) {
    console.warn('Global setup: failed to write pid file', e);
  }

  // Wait for server to become responsive
  try {
    await waitForServer(BASE_URL);
    console.log('Global setup: server is up at', BASE_URL);
  } catch (err) {
    // If server does not come up, attempt to kill child and cleanup
    try {
      if (child && child.pid) {
        process.kill(child.pid);
      }
    } catch (e) {
      /* ignore */
    }
    try { fs.unlinkSync(PID_FILE); } catch (e) { /* ignore */ }
    throw err;
  }
};

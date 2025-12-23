Playwright E2E scaffold for the World Builder UI

Quickstart (local):

1) Install dependencies (node + npm required):
   cd e2e/playwright
   npm install
   npx playwright install

2) Start the test app (in a separate terminal):
   python scripts/start_test_app.py

3) Run tests:
   npx playwright test

Notes:
- The tests assume the app is reachable at http://127.0.0.1:7870. You can override by setting E2E_BASE_URL.
- Keep tests small and deterministic; more complex flows (save-version, load-version) can be added once the smoke test is stable.

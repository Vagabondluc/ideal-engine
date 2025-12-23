import { test, expect } from '@playwright/test';

// Basic E2E smoke test for the World Builder UI. This test assumes you have
// started the app locally on the port configured in playwright.config.ts
// (by default: http://127.0.0.1:7870).

test.describe('World Builder E2E smoke', () => {
  test('loads app and shows editor, can interact with basic controls', async ({ page, baseURL }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/World Builder/i);

    // Check that world tree, editor and controls are present
    const tree = page.locator('text=World Database');
    await expect(tree).toBeVisible();

    const editor = page.locator('#wb-editor');
    await expect(editor).toBeVisible();

    const saveBtn = page.locator('button:has-text("Save")');
    await expect(saveBtn).toBeVisible();

    // Basic interaction: edit the editor (if a textarea), else ensure the element exists
    const textarea = await page.$('#wb-editor textarea');
    if (textarea) {
      await textarea.fill('E2E test content');
      await saveBtn.click();
      // Observe toast or some indication (toast root exists)
      const toast = page.locator('#wb-toast-root');
      await expect(toast).toBeVisible();
    }
  });
});

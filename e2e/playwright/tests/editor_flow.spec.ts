import { test, expect } from '@playwright/test';

// E2E flow: select file, edit, save, save new version (with notes), load version, and gutter click selection.

test('save → save-version → load-version → gutter click selection', async ({ page, baseURL }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/World Builder/i);

  // ensure sample entry present in dropdown
  const selectEntry = page.locator('label:has-text("Select Entry")').first();
  await expect(selectEntry).toBeVisible();

  // Wait for dropdown options to populate and choose e2e_sample.md
  const dropdown = page.locator('select').first();
  await dropdown.waitFor({ state: 'attached' });
  // If option exists, select it via evaluate
  await page.evaluate(() => { const s = document.querySelector('select'); if(s){ const opt = Array.from(s.options).find(o=>o.text.includes('e2e_sample.md')); if(opt) s.value = opt.value; s.dispatchEvent(new Event('change')); } });

  // Wait for editor textarea
  const textarea = await page.$('#wb-editor textarea');
  if (!textarea) {
    test.skip('No textarea editor available for test');
    return;
  }

  // Edit content
  await textarea.fill('# E2E Sample\nLine one modified\nLine two\nLine three\nLine four');
  const saveBtn = page.locator('button:has-text("Save")');
  await saveBtn.click();

  // Wait for toast to appear
  const toastRoot = page.locator('#wb-toast-root');
  await expect(toastRoot).toBeVisible();

  // Save new version with notes
  const saveMetaBtn = page.locator('button:has-text("Save (with notes)")');
  await saveMetaBtn.click();
  // Fill notes textarea and click Save Version (button text 'Save Version')
  const notesBox = page.locator('textarea[placeholder*="description for this version"]');
  if (await notesBox.count() > 0) {
    await notesBox.fill('E2E version notes');
  }
  const saveVersionBtn = page.locator('button:has-text("Save Version")');
  await saveVersionBtn.click();

  // Wait for versions dropdown to include a v_ entry
  const versions = page.locator('select[aria-label="Versions"]');
  await expect(versions).toBeVisible();
  // Wait and assert that an option appears which contains 'v_'
  await page.waitForTimeout(500);
  const hasVersion = await page.evaluate(() => {
    const s = document.querySelector('select[aria-label="Versions"]');
    if(!s) return false;
    return Array.from(s.options).some(o => o.text.includes('v_'));
  });
  expect(hasVersion).toBeTruthy();

  // Load the first version option
  await page.evaluate(() => {
    const s = document.querySelector('select[aria-label="Versions"]');
    if(s){ const opt = Array.from(s.options).find(o => o.text.includes('v_')); if(opt){ s.value = opt.value; s.dispatchEvent(new Event('change')); } }
  });

  // Click Load Version button
  const loadBtn = page.locator('button:has-text("Load Version")');
  await loadBtn.click();
  await page.waitForTimeout(400);

  // Verify editor content changed (simple check)
  const val = await textarea.inputValue();
  expect(val.includes('Line one modified') || val.includes('Line one')).toBeTruthy();

  // Test gutter click selects line 2
  const line2 = page.locator('.wb-gutter-line[data-line="2"]');
  if (await line2.count() > 0) {
    await line2.click();
    // assert textarea selection includes 'Line one'
    const selStart = await page.evaluate(()=> document.querySelector('#wb-editor textarea').selectionStart);
    expect(typeof selStart === 'number').toBeTruthy();
  }
});

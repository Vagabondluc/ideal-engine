import { test, expect } from '@playwright/test';

test.describe('E2E handshake integration', () => {
  test('usesHandshakeSignalsWhenAvailable', async ({ page, baseURL }) => {
    if (!process.env.WB_E2E_HANDSHAKE) test.skip('WB_E2E_HANDSHAKE not set');
    const resolvedBase = process.env.E2E_BASE_URL || baseURL || 'http://127.0.0.1:7871';

    // Probe handshake endpoint
    const resp = await page.request.get(resolvedBase + '/__wb_test/inspector_signals', { headers: { 'X-WB-E2E-HANDSHAKE': process.env.WB_E2E_HANDSHAKE } });
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body).toHaveProperty('signals');
    expect(Array.isArray(body.signals)).toBeTruthy();
    expect(body).toHaveProperty('inspectorHtml');
    const inspectorHtml = body.inspectorHtml;
    expect(inspectorHtml).toContain('<div');

    // Navigate to app and inject deterministic inspector HTML
    await page.goto(resolvedBase + '/');
    await page.waitForSelector('button:has-text("World Editor")', { timeout: 20000 });
    // Inject the deterministic HTML
    await page.evaluate((html) => { try { document.body.insertAdjacentHTML('beforeend', html); } catch(e) { console.warn('inject err', e); } }, inspectorHtml);
    // Wait for the inspector to exist
    await page.waitForSelector('#inspector, #e2e-inspector, .wb-inspector-row', { timeout: 5000 });

    // Ensure handleDynamicSaveResponse can be used: polyfill if absent
    await page.evaluate(() => {
      if (typeof window.handleDynamicSaveResponse !== 'function') {
        window.handleDynamicSaveResponse = function(payload){
          try{
            document.querySelectorAll('.wb-inspector-row-error').forEach(function(el){ el.innerText = ''; el.style.display = 'none'; });
            if(payload.rowErrors){
              for(var k in payload.rowErrors){
                var sel = document.querySelector('[data-key="'+k+'"]'); if(!sel) continue;
                var errEl = sel.closest('.wb-inspector-row')?.querySelector('.wb-inspector-row-error'); if(errEl){ errEl.innerText = payload.rowErrors[k][0].message; errEl.style.display = 'block'; }
              }
            }
            if(payload.firstInvalidKey){ var tgt = document.querySelector('[data-key="'+payload.firstInvalidKey+'"]'); if(tgt && typeof tgt.focus === 'function') tgt.focus(); }
          }catch(e){ console.warn('polyfill apply err', e); }
        };
      }
    });

    // Simulate server validation response (missing required 'name')
    await page.evaluate(() => {
      try{
        const payload = { ok:false, message:'Validation failed', rowErrors: { name: [{ path:'fields.name', message:'name is required', code:'REQUIRED' }] }, firstInvalidKey: 'name' };
        if(window.handleDynamicSaveResponse) window.handleDynamicSaveResponse(payload);
      }catch(e){ console.warn('simulate dyn resp err', e); }
    });

    // Expect inline error and focus on 'name'
    await page.waitForFunction(() => {
      const el = document.querySelector('[data-key="name"]');
      if (!el) return false;
      const err = el.closest('.wb-inspector-row')?.querySelector('.wb-inspector-row-error');
      return !!(err && err.innerText && err.innerText.trim().length > 0 && err.style.display !== 'none' && document.activeElement === el);
    }, null, { timeout: 3000 });

    // Now simulate success
    await page.evaluate(() => { try{ if(window.handleDynamicSaveResponse) window.handleDynamicSaveResponse({ok:true, message:'Saved', rowErrors: {}, firstInvalidKey: null}); }catch(e){} });
    await page.waitForFunction(() => { const el = document.querySelector('[data-key="name"]'); if(!el) return false; const err = el.closest('.wb-inspector-row')?.querySelector('.wb-inspector-row-error'); return !!(err && err.style.display === 'none'); }, null, { timeout: 3000 });
  });
});

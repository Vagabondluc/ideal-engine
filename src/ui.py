"""Minimal modular UI rebuilt from decomposed helpers.

This file provides a compact Gradio UI that restores the core app flows:
- Browse world files (tree + dropdown)
- View preview (Markdown)
- Edit selected file and save changes
- Run a model prompt via `src.runner.run_ollama_gen`
- Activity log panel

The goal is small, testable building blocks that can be extended gradually.
"""
from typing import Tuple
import os
import gradio as gr
try:
    from src.indexer import get_world_tree, get_world_files
except Exception:
    # allow running module under pytest importlib loader without package context
    from indexer import get_world_tree, get_world_files
from src.runner import run_ollama_gen
import src.world_builder as wb

# Small client-side toast script and styles injected into the Gradio app.
APP_STYLE = r'''
<style>
/* Toasts */
.wb-toast-container{position:fixed;right:20px;bottom:20px;z-index:9999;display:flex;flex-direction:column;gap:8px}
.wb-toast{min-width:220px;padding:10px 14px;border-radius:8px;color:#fff;font-family:system-ui;box-shadow:0 6px 18px rgba(0,0,0,0.12);opacity:0;transform:translateY(6px);transition:opacity .2s ease,transform .2s ease}
.wb-toast--info{background:#4f46e5}
.wb-toast--warn{background:#d69e2e}
.wb-toast--error{background:#ef4444}
.wb-toast.show{opacity:1;transform:translateY(0)}
/* Layout helpers to approximate the wireframe look (polish) */
.wb-left{background:linear-gradient(180deg,#ffffff, #fafafa);border:1px solid #e6e6e6;border-radius:10px;padding:10px}
.wb-editor{background:linear-gradient(180deg,#ffffff,#fbfbff);border:1px solid #e6e6e6;border-radius:10px;padding:12px}
.wb-right{background:#fff;border:1px solid #e6e6e6;border-radius:10px;padding:10px}
.wb-gutter{background:#0f1724;color:#94a3b8;border-right:1px solid #0b1220;padding:8px 4px;font-family:ui-monospace,JetBrains Mono,monospace}
.wb-gutter-line{padding:0 10px;height:22px;line-height:22px;cursor:pointer;border-radius:4px;color:#cbd5e1;font-size:12px}
.wb-gutter-line:hover{background:#111827;color:#fff}
.wb-gutter-line.active{background:#6366f1;color:#fff;font-weight:700;box-shadow:inset 3px 0 0 rgba(99,102,241,0.15)}
/* Editor font and scroll behavior */
#wb-editor, #wb-editor textarea, #wb-editor pre { font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace; font-size:13px; white-space: pre-wrap; overflow-wrap: anywhere; }
.gr-code, .gr-code pre, .gr-code code, .gr-code * { font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace; white-space: pre-wrap !important; overflow-wrap: anywhere !important; word-break: break-word !important; }
/* CodeMirror specific wrap overrides */
.cm-scroller, .cm-content, .cm-line, .cm-scroller pre { white-space: pre-wrap !important; overflow-wrap: anywhere !important; word-break: break-word !important; }
/* Additional high-specificity rules to cover Gradio/CodeMirror variants */
</gradio-container .gr-code pre, .gradio-container .gr-code code, .gradio-container .gr-code textarea, .gradio-container .gr-code .cm-scroller { white-space: pre-wrap !important; overflow-wrap: anywhere !important; word-break: break-word !important; }
.CodeMirror, .CodeMirror * { white-space: pre-wrap !important; overflow-wrap: anywhere !important; word-break: break-word !important; }
/* Grouping & spacing for Scripts + Execution areas */
.wb-scripts{padding:12px;border-radius:8px;background:linear-gradient(180deg,#ffffff,#fbfdff);border:1px solid #e6e6e6;margin-bottom:12px}
.wb-scripts .wb-scripts-header{font-weight:700;margin-bottom:8px;color:#0f1724}
.wb-execution{padding:12px;border-radius:10px;background:#ffffff;border:1px solid #e9eefb;box-shadow:0 4px 14px rgba(15,23,42,0.04);margin-top:8px}
.wb-execution .wb-exec-row{display:flex;gap:8px;align-items:center}
.wb-execution .wb-run-btn{background:#6366f1;color:#fff;padding:10px 16px;border-radius:10px;font-weight:700;font-size:15px;border:none;box-shadow:0 8px 24px rgba(99,102,241,0.12)}
.wb-execution .wb-secondary{background:#f8fafc;border:1px solid #eef2ff;color:#0f1724;padding:8px 10px;border-radius:8px}
.wb-execution .wb-note{font-size:12px;color:#6b7280;margin-left:6px}
/* Ensure readable text color on light panels and buttons */
.wb-scripts, .wb-execution, .wb-right, #wb-jump-modal { color: #0f1724 !important; }
/* Buttons on light backgrounds should use dark text unless explicitly styled */
button[style*="background:#fff"], .wb-execution .wb-secondary, .wb-scripts button { color: #0f1724 !important; }
button, .gr-button { color: inherit; }
/* Ensure generic Gradio/Block panels with light backgrounds show dark text
  Target common wrapper classes and inline-styled light backgrounds. */
.block, .wrap, .padded, .panel, .card, .hide-container { color: #0f1724 !important; }
/* Attribute selectors for inline background styles often emitted by Gradio */
[style*="background:#fff"], [style*="background: #fff"], [style*="background:rgb(255, 255, 255)"] { color: #0f1724 !important; }
[style*="background:rgba(255,255,255"], [style*="background:rgba(255, 255, 255"] { color: #0f1724 !important; }
/* Known light-mode banners used in app HTML snippets */
[style*="#eef2ff"], [style*="#f0fdf4"], [style*="#f0f0f0"], [style*="#fffbeb"] { color: #0f1724 !important; }

/* Focus highlight for tree items */
.wb-tree-focused{background:#fffbeb;border-radius:4px;padding:0 4px}
.wb-tree-focus-pulse{box-shadow:0 6px 24px rgba(99,102,241,0.14);animation:wb-pulse 1.6s ease}
@keyframes wb-pulse{0%{transform:scale(1)}50%{transform:scale(1.02)}100%{transform:scale(1)}}
[style*="border-left:4px solid #22c55e"], [style*="border-left:4px solid #d97706"], [style*="border-left:4px solid #666"] { color: #0f1724 !important; }
/* Strong/bold text in injected HTML banners (gr.HTML) can inherit white from parent wrappers.
  Force dark color for <strong> inside those banners and inside Gradio HTML components. */
.gradio-container .gr-html div[style*="#eef2ff"] strong,
.gradio-container .gr-html div[style*="#f0fdf4"] strong,
.gradio-container .gr-html div[style*="#f0f0f0"] strong,
.gradio-container .gr-html div[style*="#fffbeb"] strong,
.gradio-container .gr-html div[style*="#eef2ff"],
.gradio-container .gr-html div[style*="#f0fdf4"],
.gradio-container .gr-html div[style*="#f0f0f0"],
.gradio-container .gr-html div[style*="#fffbeb"] { color: #0f1724 !important; } .gradio-container .gr-html div[style*="#eef2ff"] *,
 .gradio-container .gr-html div[style*="#f0fdf4"] *,
 .gradio-container .gr-html div[style*="#f0f0f0"] *,
 .gradio-container .gr-html div[style*="#fffbeb"] * { color: #0f1724 !important; opacity: 1 !important; }.gradio-container .gr-html strong { color: #0f1724 !important; opacity: 1 !important; text-shadow: none !important; }
.gradio-container strong { color: #0f1724 !important; opacity: 1 !important; text-shadow: none !important; }
.wb-left strong, .wb-right strong, .wb-scripts strong, .wb-execution strong { color: #0f1724 !important; opacity: 1 !important; }
/* JS fallback: enable line wrapping on CodeMirror instances and force inline styles on runtime */
</style>
<script>
setTimeout(function(){
  try{
    // Try to enable CodeMirror lineWrapping for classic instances
    document.querySelectorAll('.CodeMirror').forEach(function(cmEl){
      try{ if(cmEl.CodeMirror && cmEl.CodeMirror.setOption) cmEl.CodeMirror.setOption('lineWrapping', true); }catch(e){}
      try{ if(cmEl.editor && cmEl.editor.setOption) cmEl.editor.setOption('lineWrapping', true); }catch(e){}
    });
    // Force inline style for CM6 containers
    document.querySelectorAll('.cm-scroller, .cm-content, .cm-line').forEach(function(el){
      try{ el.style.whiteSpace = 'pre-wrap'; el.style.overflowWrap = 'anywhere'; el.style.wordBreak = 'break-word'; }catch(e){}
    });
  }catch(e){console.warn('wrap-fallback error', e);} 
}, 250);

// Dynamic Inspector helpers
function _createInspectorRowHtml(key, title, type, value, enumChoices){
  var requiredMark = title && title.indexOf('*')!==-1 ? '<span style="color:#ef4444"> *</span>' : '';
  var html = '<div class="wb-inspector-row" style="margin-bottom:8px;padding:6px;border-bottom:1px solid #f0f0f0">';
  html += '<label style="font-weight:700;display:block;margin-bottom:6px">'+title+requiredMark+'</label>';
  if(enumChoices && enumChoices.length){
    html += '<select data-key="'+key+'" style="width:100%;padding:8px;border:1px solid #e6e6e6;border-radius:6px">';
    html += '<option value=""></option>';
    enumChoices.forEach(function(o){ html += '<option value="'+o+'" '+(o==value? 'selected':'')+'>'+o+'</option>'; });
    html += '</select>';
  } else if(type==='integer' || type==='number'){
    html += '<input data-key="'+key+'" type="number" value="'+(value||'')+'" style="width:100%;padding:8px;border:1px solid #e6e6e6;border-radius:6px" />';
  } else {
    html += '<input data-key="'+key+'" type="text" value="'+(value||'')+'" style="width:100%;padding:8px;border:1px solid #e6e6e6;border-radius:6px" />';
  }
  html += '<div class="wb-inspector-row-error" style="color:#ef4444;margin-top:6px;display:none;font-size:13px"></div>';
  html += '</div>';
  return html;
}

window.handleDynamicSaveResponse = function(payload){
  try{
    if(payload == null) return;
    if(payload.message){ try{ if(window.showWBToast) showWBToast(payload.message, payload.ok ? 'info' : 'error'); }catch(e){}
    }
    document.querySelectorAll('.wb-inspector-row-error').forEach(function(el){ el.innerText = ''; el.style.display = 'none'; });
    if(payload.rowErrors){
      for(var k in payload.rowErrors){
        var sel = document.querySelector('[data-key="'+k+'"]');
        if(!sel) continue;
        var errEl = sel.closest('.wb-inspector-row').querySelector('.wb-inspector-row-error');
        if(errEl){ errEl.innerText = payload.rowErrors[k]; errEl.style.display = 'block'; }
      }
    }
    if(payload.firstInvalidKey){ var tgt = document.querySelector('[data-key="'+payload.firstInvalidKey+'"]'); if(tgt && typeof tgt.focus === 'function') tgt.focus(); }
  }catch(e){ console.warn('handleDynamicSaveResponse err', e); }
}
</script>

(function enableWrapWithFallback(){
  var tries = 0; var maxTries = 12;
  function check(){
    tries++;
    try{
      var el = document.querySelector('.cm-scroller, .cm-content, .cm-line');
      var ok = false;
      if(el){
        var ws = window.getComputedStyle(el).whiteSpace || el.style.whiteSpace || '';
        if(ws && ws.indexOf('pre-wrap') !== -1) ok = true;
      } else {
        var pre = document.querySelector('.gr-code pre, .gr-code code');
        if(pre){ var ws = window.getComputedStyle(pre).whiteSpace || pre.style.whiteSpace || ''; if(ws && ws.indexOf('pre-wrap') !== -1) ok = true; }
      }
      // If computed style indicates wrapping OR scroll dims suggest wrap, mark ok
      try{
        if(el){
          var ws = window.getComputedStyle(el).whiteSpace || el.style.whiteSpace || '';
          var wrappedByStyle = (ws && ws.indexOf('pre-wrap') !== -1);
          var wrappedByScroll = (el.scrollWidth <= el.clientWidth + 2);
          if(wrappedByStyle || wrappedByScroll){
            window.wbActionCallback(JSON.stringify({action:'wrap_status', status:'ok'}));
            return;
          }
        } else {
          var pre = document.querySelector('.gr-code pre, .gr-code code');
          if(pre){ var ws = window.getComputedStyle(pre).whiteSpace || pre.style.whiteSpace || ''; if(ws && ws.indexOf('pre-wrap') !== -1){ window.wbActionCallback(JSON.stringify({action:'wrap_status', status:'ok'})); return; } }
        }
      }catch(e){/*ignore*/}
      if(tries >= maxTries){
        // fallback: extract editor content and ask server to switch to wrapped textbox
        try{
          var editorEl = findEditor();
          var text = editorEl ? getText(editorEl) : '';
          window.wbActionCallback(JSON.stringify({action:'switch_to_textbox_auto', content: text}));
          window.wbActionCallback(JSON.stringify({action:'wrap_status', status:'autofallback'}));
          showWBToast('Wrapping not available; switching to wrapped textbox', 'warn', {ttl:4000});
        }catch(e){ console.warn('wrap autofallback err', e); }
        return;
      }
      // re-apply styles & try CM APIs
      document.querySelectorAll('.CodeMirror').forEach(function(cmEl){ try{ if(cmEl.CodeMirror && cmEl.CodeMirror.setOption) cmEl.CodeMirror.setOption('lineWrapping', true); }catch(e){} try{ if(cmEl.editor && cmEl.editor.setOption) cmEl.editor.setOption('lineWrapping', true); }catch(e){} });
      document.querySelectorAll('.cm-scroller, .cm-content, .cm-line').forEach(function(el){ try{ el.style.whiteSpace = 'pre-wrap'; el.style.overflowWrap = 'anywhere'; el.style.wordBreak = 'break-word'; }catch(e){} });
      setTimeout(check, 300);
    }catch(e){ console.warn('wrap check err', e); if(tries < maxTries) setTimeout(check, 300); }
  }
  setTimeout(check, 300);
})();

</script>

<!-- Jump-to-line modal markup -->
<div id="wb-jump-modal" style="display:none;position:fixed;left:50%;top:40%;transform:translate(-50%,-50%);background:#fff;padding:12px;border-radius:8px;box-shadow:0 6px 18px rgba(0,0,0,0.12);z-index:99999">
  <div style="font-weight:600;margin-bottom:6px">Jump to line</div>
  <input id="wb-jump-input" type="number" min="1" placeholder="Line number" style="width:140px;padding:6px;border:1px solid #e5e7eb;border-radius:6px" />
  <button id="wb-jump-go" style="margin-left:8px;padding:6px 10px;border-radius:6px;background:#4f46e5;color:#fff;border:none">Go</button>
  <button id="wb-jump-cancel" style="margin-left:6px;padding:6px;border-radius:6px;border:1px solid #e5e7eb;background:#fff">Cancel</button>
</div>

<!-- Floating context menu for tree (hidden by default) -->
<div id='wb-tree-context-menu' style='display:none;position:fixed;z-index:100000;background:#fff;border:1px solid #e6e6e6;border-radius:6px;padding:6px;box-shadow:0 6px 18px rgba(0,0,0,0.12);font-family:system-ui;'>
  <div class='wb-tree-context-item' data-op='new_folder' style='padding:6px;cursor:pointer'>📁 New Folder</div>
  <div class='wb-tree-context-item' data-op='new_card' style='padding:6px;cursor:pointer'>📝 New Card</div>
  <div class='wb-tree-context-item' data-op='rename' style='padding:6px;cursor:pointer'>✏️ Rename</div>
  <div class='wb-tree-context-item' data-op='duplicate' style='padding:6px;cursor:pointer'>🔁 Duplicate</div>
  <div class='wb-tree-context-item' data-op='delete' style='padding:6px;cursor:pointer'>🗑 Delete</div>
  <div class='wb-tree-context-item' data-op='restore' style='padding:6px;cursor:pointer;color:#0f766e'>♻️ Restore</div>
</div>

<!-- Modal for context actions (rename, new folder, delete confirm) -->
<div id='wb-context-modal' style='display:none;position:fixed;left:50%;top:40%;transform:translate(-50%,-50%);background:#fff;padding:12px;border-radius:8px;box-shadow:0 6px 18px rgba(0,0,0,0.12);z-index:99999;min-width:320px;'>
  <div id='wb-context-modal-title' style='font-weight:600;margin-bottom:8px'>Action</div>
  <div id='wb-context-modal-body' style='margin-bottom:8px;'><input id='wb-context-modal-input' placeholder='' style='width:100%;padding:8px;border:1px solid #e5e7eb;border-radius:6px' /></div>
  <div style='display:flex;gap:8px;justify-content:flex-end'><button id='wb-context-modal-cancel' style='padding:6px;border-radius:6px;border:1px solid #e5e7eb;background:#fff'>Cancel</button><button id='wb-context-modal-confirm' style='padding:6px;border-radius:6px;background:#4f46e5;color:#fff;border:none'>Confirm</button></div>
</div>

<div id='wb-toast-root' class='wb-toast-container'></div>
<script>
window.showWBToast = function (msg, level='info', opts={}) {
  try{
    var root = document.getElementById('wb-toast-root');
    if(!root){ console.warn('Toast root not found'); return; }
    var div = document.createElement('div');
    div.className = 'wb-toast wb-toast--' + (level || 'info');
    div.innerHTML = msg;
    root.appendChild(div);
    requestAnimationFrame(function(){ div.classList.add('show'); });
    var ttl = (opts.ttl === undefined) ? 4000 : opts.ttl;
    var timer = setTimeout(function(){ div.classList.remove('show'); setTimeout(function(){ root.removeChild(div); },250); }, ttl);
    div.addEventListener('click', function(){ clearTimeout(timer); div.classList.remove('show'); setTimeout(function(){ if(div.parentNode) div.parentNode.removeChild(div); },250); });
    return div;
  }catch(e){ console.warn('showWBToast error', e); }
}
</script>
<script>
window.wbActionCallback = function(json){
  try{
    var el = document.getElementById('wb-action-box') || document.getElementById('wb-tree-action-box');
    if(!el){ console.warn('wb-action-box not found'); return; }
    el.value = json;
    el.dispatchEvent(new Event('input', {bubbles:true}));
    el.dispatchEvent(new Event('change', {bubbles:true}));
  }catch(e){ console.warn('wbActionCallback err', e); }
};
document.addEventListener('click', function(e){
  try{
    var btn = e.target.closest('button[data-retry-id], button[data-open-folder]');
    if(!btn) return;
    if(btn.dataset.retryId){ window.wbActionCallback(JSON.stringify({action:'retry', retry_id: btn.dataset.retryId})); }
    else if(btn.dataset.openFolder){ window.wbActionCallback(JSON.stringify({action:'open_folder', path: btn.dataset.openFolder})); }
  }catch(e){ console.warn('wbAction listener err', e); }
});

</script>

<script>
// Delegated handler for dynamic inspector Save button (works even if inline scripts don't run)
document.addEventListener('click', function(e){
  try{
    var btn = e.target && e.target.closest && e.target.closest('#wb-inspector-save');
    if(!btn) return;
    var uuid = btn.getAttribute('data-uuid') || null;
    var form = btn.closest('div');
    if(!form) return;
    var inputs = form.querySelectorAll('[data-key]');
    var out = {};
    inputs.forEach(function(i){ var k = i.getAttribute('data-key'); var v = i.value; out[k] = v; });
    window.wbActionCallback(JSON.stringify({action:'save_card_form_dynamic', uuid: uuid, formData: out}));
  }catch(e){ console.warn('inspector save delegated err', e); }
});
</script>

<!-- Tree UI handlers: emit JSON to #wb-tree-action-box on single-click, double-click (open), and right-click context ops -->
<script>
(function initTreeHandlers(){
  var dblMs = 300;
  var lastClick = 0;
  function findTreeRoot(){
    return document.querySelector('#wb-tree-code');
  }
  function findTreePre(){
    var root = findTreeRoot(); if(!root) return null;
    return root.querySelector('pre') || root;
  }
  function sendTreeAction(obj){
    try{
      var ab = document.getElementById('wb-tree-action-box') || document.getElementById('wb-action-box');
      if(!ab){ console.warn('wb-tree-action-box not found'); return; }
      ab.value = JSON.stringify(obj);
      ab.dispatchEvent(new Event('input', {bubbles:true}));
      ab.dispatchEvent(new Event('change', {bubbles:true}));
    }catch(e){ console.warn('sendTreeAction error', e); }
  }

  // Single click => select (debounced to allow dblclick to take precedence)
  document.addEventListener('click', function(e){
    try{
      var el = e.target;
      var root = el && el.closest && el.closest('#wb-tree-code');
      if(!root) return;
      var txt = (el.innerText || el.textContent || '').trim();
      if(!txt) return;
      var now = Date.now();
      if(now - lastClick < dblMs){
        // treat as double-click
        sendTreeAction({action:'open', path: txt});
        lastClick = 0;
        return;
      }
      lastClick = now;
      setTimeout(function(){ if(Date.now() - lastClick >= dblMs){ sendTreeAction({action:'select', path: txt}); } }, dblMs + 10);
    }catch(e){/*ignore*/}
  });

  // Provide a function to focus a tree item by text (called from server via script in toast)
  window.focusTreeItem = function(targetText){
    try{
      var pre = document.querySelector('#wb-tree-code pre') || document.querySelector('#wb-tree-code');
      if(!pre) return;
      var html = pre.innerHTML;
      // escape targetText for use in regex
      var esc = targetText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      var re = new RegExp(esc);
      if(!re.test(html)){
        // try matching just the file name
        var parts = targetText.split('/'); var fn = parts[parts.length-1];
        var re2 = new RegExp(fn);
        if(!re2.test(html)) return;
        // replace first occurrence of file name
        html = html.replace(re2, '<span class="wb-tree-focused">'+fn+'</span>');
      } else {
        html = html.replace(re, '<span class="wb-tree-focused">'+targetText+'</span>');
      }
      pre.innerHTML = html;
      // scroll focus into view
      var el = pre.querySelector('.wb-tree-focused');
      if(el){ el.scrollIntoView({block:'center', behavior:'smooth'}); setTimeout(function(){ el.classList.add('wb-tree-focus-pulse'); setTimeout(function(){ el.classList.remove('wb-tree-focus-pulse'); }, 1800); }, 80); }
    }catch(e){ console.warn('focusTreeItem err', e); }
  };


  // Right-click context menu -> show floating context menu and emit selected op
  document.addEventListener('contextmenu', function(e){
    try{
      var el = e.target;
      var root = el && el.closest && el.closest('#wb-tree-code');
      if(!root) return;
      e.preventDefault();
      var txt = (el.innerText || el.textContent || '').trim();
      if(!txt) return;
      // Show floating menu at mouse position
      var menu = document.getElementById('wb-tree-context-menu');
      if(!menu) return;
      menu.style.display = 'block';
      menu.style.left = (e.clientX + 4) + 'px';
      menu.style.top = (e.clientY + 4) + 'px';
      menu.dataset.targetPath = txt;
    }catch(e){/*ignore*/}
  });

  // Hide menu on Escape or any click outside
  document.addEventListener('keydown', function(e){ if(e.key === 'Escape'){ var m = document.getElementById('wb-tree-context-menu'); if(m){ m.style.display='none'; } } });
  document.addEventListener('click', function(e){ try{ var menu = document.getElementById('wb-tree-context-menu'); if(!menu) return; if(!e.target.closest('#wb-tree-context-menu')){ menu.style.display = 'none'; } }catch(e){} });

  // Context menu click handler
  document.addEventListener('click', function(e){
    try{
      var item = e.target.closest && e.target.closest('.wb-tree-context-item');
      if(!item) return;
      var op = item.dataset.op;
      var menu = document.getElementById('wb-tree-context-menu');
      var path = menu && menu.dataset && menu.dataset.targetPath ? menu.dataset.targetPath : '';

      // Helper to show modal
      function showModal(title, placeholder, onConfirm){
        var modal = document.getElementById('wb-context-modal');
        var titleEl = document.getElementById('wb-context-modal-title');
        var input = document.getElementById('wb-context-modal-input');
        var cancel = document.getElementById('wb-context-modal-cancel');
        var confirm = document.getElementById('wb-context-modal-confirm');
        titleEl.innerText = title;
        input.value = '';
        input.placeholder = placeholder || '';
        modal.style.display = 'block';
        input.focus();
        function cleanup(){ modal.style.display='none'; cancel.removeEventListener('click', onCancel); confirm.removeEventListener('click', onConfirmClick); }
        function onCancel(){ cleanup(); }
        function onConfirmClick(){ var v = input.value; cleanup(); onConfirm(v); }
        cancel.addEventListener('click', onCancel);
        confirm.addEventListener('click', onConfirmClick);
      }

      // Rename: open modal
      if(op === 'rename'){
        showModal('Rename ' + path, 'New name', function(newName){ if(!newName) return; sendTreeAction({action:'context', op: op, path: path, new_name: newName}); });
        menu.style.display = 'none';
        return;
      }

      // New folder: ask for folder name
      if(op === 'new_folder'){
        showModal('New folder under ' + path, 'Folder name', function(name){ if(!name) return; sendTreeAction({action:'context', op: op, path: path, name: name}); });
        menu.style.display = 'none';
        return;
      }

      // Delete: confirmation modal
      if(op === 'delete'){
        showModal('Delete ' + path + '? (type HARD to permanently remove, leave blank for soft)', 'Type HARD to hard delete', function(resp){ var hard = (resp || '').trim().toUpperCase() === 'HARD'; sendTreeAction({action:'context', op: op, path: path, hard: hard}); });
        menu.style.display = 'none';
        return;
      }

      // Restore: simple confirm modal
      if(op === 'restore'){
        showModal('Restore ' + path + '?', '', function(v){ sendTreeAction({action:'context', op: op, path: path}); });
        menu.style.display = 'none';
        return;
      }

      // Default: send op
      sendTreeAction({action:'context', op: op, path: path});
      menu.style.display = 'none';
    }catch(e){/*ignore*/}
  });
})();
</script>
<script>
// Gutter sync: update line numbers and scroll sync for the editor/gutter pair
(function(){
  function findEditor(){
    var el = document.getElementById('wb-editor');
    if(!el) return null;
    var selectors = ['textarea','[contenteditable="true"]','.cm-scroller','.CodeMirror-scroll','pre'];
    for(var i=0;i<selectors.length;i++){
      var s = el.querySelector(selectors[i]);
      if(s) return s;
    }
    return el;
  }
  function getText(el){
    if(!el) return '';
    try{
      if(el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') return el.value || '';
    }catch(e){}
    return el.textContent || '';
  }
  function updateGutter(){
    var ed = findEditor();
    var gutterLines = document.getElementById('wb-gutter-lines');
    if(!gutterLines || !ed) return;
    var text = getText(ed) || '';
    var lines = text.split('\n');
    var out = '';
    for(var i=0;i<lines.length;i++){
      out += "<div class='wb-gutter-line' data-line='"+(i+1)+"'>"+(i+1)+"</div>";
    }
    if(gutterLines.innerHTML !== out) gutterLines.innerHTML = out;
  }
  function syncScroll(){
    var ed = findEditor();
    var gutter = document.getElementById('wb-gutter');
    if(!ed || !gutter) return;
    try{
      var edScrollTop = 0;
      if(typeof ed.scrollTop === 'number') edScrollTop = ed.scrollTop;
      else if(ed.parentElement && typeof ed.parentElement.scrollTop === 'number') edScrollTop = ed.parentElement.scrollTop;
      gutter.scrollTop = edScrollTop;
    }catch(e){/*ignore*/}
  }
  // click handler to jump caret to start of clicked line
  function selectLineInEditor(line){
    var ed = findEditor();
    if(!ed) return;
    var text = getText(ed) || '';
    var parts = text.split('\n');
    var offset = 0;
    for(var i=0;i<line-1 && i<parts.length;i++){ offset += parts[i].length + 1; }
    var lineLen = (parts[line-1] || '').length;
    if(ed.tagName === 'TEXTAREA' || ed.tagName === 'INPUT'){
      ed.focus();
      try{ ed.selectionStart = offset; ed.selectionEnd = offset + lineLen; }catch(e){}
      updateActiveGutter();
      return;
    }
    try{
      ed.focus();
      var win = ed.ownerDocument.defaultView || window;
      if(win.getSelection){
        var sel = win.getSelection(); sel.removeAllRanges();
        var range = ed.ownerDocument.createRange();
        var walker = ed.ownerDocument.createTreeWalker(ed, NodeFilter.SHOW_TEXT, null, false);
        var charCount = 0; var foundNode = null;
        while(walker.nextNode()){
          var n = walker.currentNode; var len = n.nodeValue.length;
          if(charCount + len >= offset){ foundNode = n; break; }
          charCount += len;
        }
        if(foundNode){
          var start = offset - charCount;
          var end = start + lineLen;
          range.setStart(foundNode, start);
          // compute end node/offset
          var rem = end - (foundNode.nodeValue.length - start);
          var endNode = foundNode; var endOffset = start + Math.min(lineLen, foundNode.nodeValue.length - start);
          while(rem > 0 && endNode.nextSibling){ endNode = endNode.nextSibling; if(endNode.nodeType === Node.TEXT_NODE){ var take = Math.min(rem, endNode.nodeValue.length); endOffset = take; rem -= take; } else { /*skip*/ } }
          range.setEnd(endNode, endOffset);
          sel.addRange(range);
          updateActiveGutter();
        }
      }
    }catch(e){/*best-effort*/}
  }

  function gutterClickHandler(e){
    try{
      var target = e.target.closest('.wb-gutter-line');
      if(!target) return;
      var line = parseInt(target.dataset.line,10);
      if(!line) return;
      selectLineInEditor(line);
    }catch(e){/*ignore*/}
  }
  document.addEventListener('click', function(e){
    try{ gutterClickHandler(e); }catch(e){/*ignore*/}
  });

  // Jump-to-line handlers
  function showJumpToLinePrompt(){
    var m = document.getElementById('wb-jump-modal');
    if(!m) return;
    m.style.display = 'block';
    var input = document.getElementById('wb-jump-input');
    if(input){ input.value = ''; input.focus(); }
  }
  function hideJumpToLinePrompt(){
    var m = document.getElementById('wb-jump-modal'); if(!m) return; m.style.display = 'none';
  }
  function submitJump(){
    var input = document.getElementById('wb-jump-input'); if(!input) return;
    var v = parseInt(input.value, 10);
    if(!v || v < 1) return;
    selectLineInEditor(v);
    hideJumpToLinePrompt();
  }
  document.addEventListener('click', function(e){
    var go = e.target.closest && e.target.closest('#wb-jump-go');
    var cancel = e.target.closest && e.target.closest('#wb-jump-cancel');
    if(go){ submitJump(); }
    if(cancel){ hideJumpToLinePrompt(); }
  });
  document.addEventListener('keydown', function(e){
    var m = document.getElementById('wb-jump-modal'); if(m && m.style.display === 'block'){
      if(e.key === 'Enter'){ submitJump(); }
      if(e.key === 'Escape'){ hideJumpToLinePrompt(); }
    }
  });

  function updateActiveGutter(){
    var ed = findEditor();
    var gutterLines = document.getElementById('wb-gutter-lines');
    if(!gutterLines || !ed) return;
    var selStart = 0, selEnd = 0;
    try{
      if(ed.tagName === 'TEXTAREA' || ed.tagName === 'INPUT'){
        selStart = ed.selectionStart || 0; selEnd = ed.selectionEnd || selStart;
      } else {
        var win = ed.ownerDocument.defaultView || window; var s = win.getSelection();
        if(s && s.rangeCount){
          var r = s.getRangeAt(0); selStart = getOffsetWithin(ed, r.startContainer, r.startOffset); selEnd = getOffsetWithin(ed, r.endContainer, r.endOffset);
        } else { selStart = selEnd = 0; }
      }
    }catch(e){ /* ignore */ }
    var text = getText(ed) || '';
    var before = text.slice(0, selStart); var startLine = before.split('\n').length;
    var beforeEnd = text.slice(0, selEnd); var endLine = beforeEnd.split('\n').length;
    // clear previous
    var nodes = gutterLines.querySelectorAll('.wb-gutter-line');
    nodes.forEach(function(n){ n.classList.remove('active'); });
    for(var i=startLine;i<=endLine;i++){
      var node = gutterLines.querySelector('.wb-gutter-line[data-line="'+i+'"]'); if(node) node.classList.add('active');
    }
  }

  function getOffsetWithin(root, node, offset){
    var walker = root.ownerDocument.createTreeWalker(root, NodeFilter.SHOW_TEXT, null, false);
    var total = 0; var n;
    while(walker.nextNode()){
      n = walker.currentNode; if(n === node){ return total + offset; } total += n.nodeValue.length;
    }
    return total;
  }

  // hook selection changes
  setTimeout(function(){
    updateGutter(); updateActiveGutter();
    setInterval(function(){ updateGutter(); updateActiveGutter(); }, 700);
    var root = document.getElementById('wb-editor');
    var inner = findEditor();
    if(inner && inner !== root){
      inner.addEventListener('scroll', syncScroll);
      inner.addEventListener('input', function(){ updateGutter(); updateActiveGutter(); });
      inner.addEventListener('keyup', function(){ updateGutter(); updateActiveGutter(); });
      inner.addEventListener('mouseup', function(){ updateActiveGutter(); });
    }
    document.addEventListener('selectionchange', function(){ updateActiveGutter(); });
    root.addEventListener('scroll', syncScroll);
    window.addEventListener('resize', updateGutter);

    // Keyboard shortcut: Ctrl/Cmd+G to open Jump to Line prompt
    document.addEventListener('keydown', function(e){
      if((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'g'){
        e.preventDefault();
        showJumpToLinePrompt();
      }
    });
  }, 500);
  // attach after render
  setTimeout(function(){
    updateGutter();
    setInterval(updateGutter, 700);
    var root = document.getElementById('wb-editor');
    if(!root) return;
    var inner = findEditor();
    if(inner && inner !== root){
      inner.addEventListener('scroll', syncScroll);
      inner.addEventListener('input', updateGutter);
      inner.addEventListener('keyup', updateGutter);
    }
    root.addEventListener('scroll', syncScroll);
    window.addEventListener('resize', updateGutter);
  }, 500);
})();
</script>
'''


import json
import time

def show_toast(message: str, level: str = 'info') -> str:
    """Return a small HTML snippet that triggers the frontend toast handler.

    Uses a lightweight JSON encoding to safely embed the message in inline JS.
    """
    try:
        payload = json.dumps(str(message))
        return f"<script>showWBToast({payload}, '{level}');</script>"
    except Exception:
        # Fail-safe fallback
        payload = json.dumps(str(message))
        return f"<script>showWBToast({payload}, 'info');</script>"


# -------------------- Inspector helpers (UI-friendly) --------------------

MAX_INSPECTOR_FIELDS = 20


def build_inspector_rows(fields: list) -> list:
    """Convert a list of field descriptors into a list-of-rows.

    Each row: [key, title, type, value, required, enum]
    """
    if not fields:
        return []
    rows = []
    for f in fields:
        key = f.get('key')
        title = f.get('title') or key
        ftype = f.get('type') or 'string'
        val = f.get('value') if f.get('value') is not None else ''
        required = bool(f.get('required'))
        enum = f.get('enum') if f.get('enum') is not None else None
        rows.append([key, title, ftype, val, required, enum])
    return rows


def rows_to_component_lists(rows: list):
    """Convert rows into parallel lists representing component values.

    Returns:
      keys, types, text_values, num_values, dropdown_values, dropdown_choices
    """
    keys = [''] * MAX_INSPECTOR_FIELDS
    types = [''] * MAX_INSPECTOR_FIELDS
    text_vals = [''] * MAX_INSPECTOR_FIELDS
    num_vals = [None] * MAX_INSPECTOR_FIELDS
    dd_vals = [''] * MAX_INSPECTOR_FIELDS
    dd_choices = [None] * MAX_INSPECTOR_FIELDS
    for i, r in enumerate(rows or []):
        if i >= MAX_INSPECTOR_FIELDS:
            break
        # support rows with optional enum at index 5
        if len(r) == 6:
            key, title, ftype, val, required, enum = r
        else:
            key, title, ftype, val, required = r
            enum = None
        keys[i] = key
        types[i] = ftype
        if ftype in ('integer', 'number'):
            try:
                num_vals[i] = int(val) if str(val).strip() != '' else None
            except Exception:
                num_vals[i] = None
            text_vals[i] = ''
        else:
            text_vals[i] = str(val) if val is not None else ''
        # if enum provided, set dropdown choices and value
        dd_vals[i] = val if enum else ''
        dd_choices[i] = list(enum) if enum else None
    return keys, types, text_vals, num_vals, dd_vals, dd_choices


def _render_inspector_html_for_card(uuid, fields):
    """Build a dynamic HTML form for the inspector with inputs data-key'ed (module-level)."""
    if not fields:
        return "<div style='color:#666'>No fields defined for this schema.</div>"
    parts = ["<div style='padding:8px;max-width:640px'>", f"<div style='margin-bottom:8px;font-weight:700'>Inspector — {uuid}</div>"]
    for f in fields:
        key = wb.html_escape(f.get('key'))
        title = wb.html_escape(f.get('title') or key)
        ftype = f.get('type') or 'string'
        val = wb.html_escape(f.get('value')) if f.get('value') is not None else ''
        enum = f.get('enum')
        required = f.get('required')
        req_html = " <span style='color:#ef4444'>*</span>" if required else ""
        parts.append(f"<div class='wb-inspector-row' style='margin-bottom:8px;padding:6px;border-bottom:1px solid #f7f7f7'>")
        parts.append(f"<label style='font-weight:700;display:block;margin-bottom:6px'>{title}{req_html}</label>")
        if enum:
            parts.append(f"<select data-key=\"{key}\" style='width:100%;padding:8px;border:1px solid #e6e6e6;border-radius:6px'>")
            parts.append("<option value=''></option>")
            for o in enum:
                sel = "selected" if str(o) == str(val) else ""
                parts.append(f"<option value=\"{wb.html_escape(o)}\" {sel}>{wb.html_escape(o)}</option>")
            parts.append("</select>")
        elif ftype in ('integer', 'number'):
            parts.append(f"<input data-key=\"{key}\" type=\"number\" value=\"{val}\" style='width:100%;padding:8px;border:1px solid #e6e6e6;border-radius:6px' />")
        else:
            parts.append(f"<input data-key=\"{key}\" type=\"text\" value=\"{val}\" style='width:100%;padding:8px;border:1px solid #e6e6e6;border-radius:6px' />")
        parts.append("<div class='wb-inspector-row-error' style='color:#ef4444;margin-top:6px;display:none;font-size:13px'></div>")
        parts.append("</div>")
    parts.append(f"<div style='display:flex;gap:8px;justify-content:flex-end;margin-top:12px'><button id=\"wb-inspector-save\" data-uuid=\"{uuid}\" style='background:#4f46e5;color:#fff;padding:8px 12px;border-radius:6px;border:none'>Save</button></div>")
    # Inline script for Save handling: do client-side minimal validation and then POST via wbActionCallback
    script = r"<script>document.getElementById('wb-inspector-save').addEventListener('click', function(){try{var form = this.closest('div'); var inputs = form.querySelectorAll('[data-key]'); var out = {}; var missing = []; inputs.forEach(function(i){ var k = i.getAttribute('data-key'); var v = i.value; out[k] = v; if(i instanceof HTMLInputElement && i.type === 'number'){ /* allow empty */ } }); window.wbActionCallback(JSON.stringify({action:'save_card_form_dynamic', uuid:'" + uuid + "', formData: out})); }catch(e){console.warn('inspector save err', e);} });</script>"
    parts.append(script)
    return '\n'.join(parts)


def inspector_save_handler(relpath: str, keys: list, types: list, text_values: list, num_values: list, dropdown_values: list, base_dir: str | None = None):
    """Validate component lists and persist formData.

    Returns (toast_html, error_html) where error_html is empty on success.
    """
    try:
        if not relpath or not relpath.startswith('cards/'):
            return show_toast('Inspector save: no card selected', 'error'), ""
        import re
        m = re.search(r"([0-9a-fA-F\-]{36})", relpath)
        if not m:
            return show_toast('Inspector save: unable to extract card UUID', 'error'), ""
        uuid = m.group(1)
        # build formData and validate
        formData = {}
        row_errors = [''] * MAX_INSPECTOR_FIELDS
        for i in range(MAX_INSPECTOR_FIELDS):
            key = keys[i] if i < len(keys) and keys[i] else ''
            if not key:
                continue
            ftype = types[i] if i < len(types) and types[i] else 'text'
            txt = text_values[i] if i < len(text_values) else ''
            num = num_values[i] if i < len(num_values) else None
            dd = dropdown_values[i] if i < len(dropdown_values) else ''
            # determine value
            if ftype in ('integer', 'number'):
                if num is None or (isinstance(num, str) and str(num).strip() == ''):
                    # treat empty as missing; validation only enforced if required later
                    val = None
                else:
                    try:
                        val = int(num)
                    except Exception:
                        row_errors[i] = f"Field '{key}' requires an integer value"
                        continue
            elif isinstance(dd, (list, tuple)) and len(dd) > 0:
                val = dd
            else:
                val = txt
            # Check required by looking up an external schema if needed
            from src.world_builder import get_card_form_fields
            try:
                fields = get_card_form_fields(uuid, base_dir=base_dir) if base_dir else get_card_form_fields(uuid)
                req = False
                if fields:
                    for f in fields:
                        if f.get('key') == key:
                            req = bool(f.get('required'))
                            break
                if req and (val is None or (isinstance(val, str) and val.strip() == '')):
                    row_errors[i] = f"Field '{key}' is required"
                    continue
            except Exception:
                # Safe fallback: treat as not required when we cannot load schema
                pass
            if val is not None:
                formData[key] = val
        # If any per-row errors exist, return them with a global summary
        if any(r for r in row_errors):
            summarized = [r for r in row_errors if r]
            err_html = "<div style='color:#ef4444;padding:8px;border:1px solid #f5a3a3;border-radius:6px;'><strong>Validation error:</strong><ul>" + ''.join(f"<li>{e}</li>" for e in summarized) + "</ul></div>"
            return (show_toast('Validation failed', 'error'), err_html, *row_errors)
        # Persist
        import src.world_builder as wb
        ok = wb.save_card_form_fields(uuid, formData, base_dir=base_dir) if base_dir else wb.save_card_form_fields(uuid, formData)
        if ok:
            # no row errors
            return (show_toast('Saved form', 'info'), "", *([''] * MAX_INSPECTOR_FIELDS))
        else:
            return (show_toast('Save failed', 'error'), "<div style='color:#ef4444'>Save failed</div>", *([''] * MAX_INSPECTOR_FIELDS))
    except Exception as e:
        return (show_toast(f'Inspector save error: {e}', 'error'), f"<div style='color:#ef4444'>Inspector save error: {e}</div>", *([''] * MAX_INSPECTOR_FIELDS))

def refresh_tree_ui() -> Tuple[str, dict]:
    tree = get_world_tree()
    files = get_world_files()
    return tree, {'choices': files, 'value': (files[0] if files else None)}


def load_file(relpath: str):
    if not relpath:
        return "", "(no file selected)"
    path = wb.Path('world_db') / relpath
    try:
        with path.open('r', encoding='utf-8') as fh:
            content = fh.read()
        return content, wb.get_activity_log_html()
    except Exception as e:
        return wb.format_error_enhanced('Unable to read file', detail=str(e)), wb.get_activity_log_html()


def save_file(relpath: str, content: str):
    # Use the existing helper which returns a tuple; adapt to simplified UI outputs.
    try:
        res = wb.save_editor(relpath, content)
        # save_editor returns (toast_script, content, tree_upd, files_upd, ctx_html, "", activity_html)
        if isinstance(res, tuple):
            toast = res[0]
            out_content = res[1]
            # ignore tree/files/activity returned by save_editor for this minimal UI
            return toast, out_content, wb.get_world_tree(), wb.get_activity_log_html()
        else:
            return f"<script>showWBToast({gr.utils.encode_to_json(str(res))}, 'info');</script>", content, wb.get_world_tree(), wb.get_activity_log_html()
    except Exception as e:
        return wb.format_error_enhanced('Save failed', detail=str(e)), content, wb.get_world_tree(), wb.get_activity_log_html()

def run_model(prompt: str, model: str, temperature: float, is_running_state: bool = False):
    """Execute Ollama and return (output_text, toast_html).

    For tests and the minimal UI consumer, return a tuple where the second
    element is an info/error toast HTML snippet to display status.
    """
    try:
        ok, payload = run_ollama_gen(prompt, model, temperature, timeout=120)
        if ok:
            out = payload.get('stdout', '')
            return out, show_toast('✅ Model run finished', 'info')
        else:
            return '', show_toast('❌ Model run failed', 'error')
    except Exception as e:
        return '', show_toast(f'❌ Model run error: {e}', 'error')


def handle_action_json(action_json: str):
    """Handle an action JSON (used by JS bridge). ALWAYS returns a 4-tuple:
       (toast_html, prompt_editor_update, prompt_editor_text_update, wrap_status_update)
    """
    try:
        payload = json.loads(action_json or '{}')
    except Exception:
        payload = {}
    default = (show_toast('Unrecognized action','warn'), gr.update(), gr.update(), gr.update(value='unknown'))
    if not payload or 'action' not in payload:
        return default

    act = payload.get('action')
    if act == 'retry':
        rid = payload.get('retry_id')
        res = wb.perform_retry(rid)
        toast = res if isinstance(res, str) else show_toast(str(res))
        return toast, gr.update(), gr.update(), gr.update(value='retry')

    if act == 'open_folder':
        path = payload.get('path')
        ok, msg = wb.open_folder(path)
        return show_toast(msg, 'info' if ok else 'error'), gr.update(), gr.update(), gr.update(value='open_folder')

    if act == 'create_card':
        # payload: {action: 'create_card', type, schema_id, title, formData, markdown}
        card_type = payload.get('type')
        schema_id = payload.get('schema_id')
        title = payload.get('title', 'Untitled')
        formData = payload.get('formData', {})
        markdown = payload.get('markdown', '')
        toast, new_uuid = wb.create_card_from_payload(card_type, schema_id, title, formData, markdown)
        # return toast and a small update that instructs client to refresh the tree view
        return toast, gr.update(), gr.update(), gr.update(value='card_created:' + (new_uuid or ''))

    # Test-only: create a card deterministically (only works when WB_E2E_HANDSHAKE=1)
    if act == 'test_create_card':
        try:
            import os as _os
            if not _os.environ.get('WB_E2E_HANDSHAKE'):
                return show_toast('Test create not enabled', 'error'), gr.update(), gr.update(), gr.update(value='test_create_not_enabled')
            toast, new_uuid = wb.create_card_from_payload('npc', 'npc_antagonist_v1', 'E2E NPC', {}, '# New NPC')
            # write inspector ready trace and emit handshake script
            try:
                from pathlib import Path
                Path('world_db').mkdir(parents=True, exist_ok=True)
                p = Path('world_db') / '.trace'
                p.write_text((p.read_text(encoding='utf-8') if p.exists() else '') + f"CREATED {new_uuid} {time.time()}\nINSPECTOR_READY {new_uuid} {time.time()}\n", encoding='utf-8')
            except Exception:
                pass
            import json as _json
            hs = f"<script>try{{ window.__wb_inspector_ready = {_json.dumps(new_uuid)}; window.dispatchEvent(new CustomEvent('wb:inspector_ready', {{detail: {{uuid: {_json.dumps(new_uuid)} }} }})); }}catch(e){{console.warn('handshake err',e);}}</script>"
            if isinstance(toast, str):
                toast = toast + hs
            else:
                toast = show_toast('Created E2E card','info') + hs
            return toast, gr.update(), gr.update(), gr.update(value='test_card_created:' + (new_uuid or ''))
        except Exception as e:
            return show_toast(f'Test create failed: {e}', 'error'), gr.update(), gr.update(), gr.update(value='test_create_error')

    if act == 'save_card_form_dynamic':
        # payload: {action: 'save_card_form_dynamic', uuid: <uuid>, formData: {k: v}}
        uuid = payload.get('uuid')
        formData = payload.get('formData', {})
        # Reuse validation logic from inspector_save_handler by mapping keys/types via schema
        try:
            # get fields from schema to know required flags and types
            fields = wb.get_card_form_fields(uuid) or []
            # Build keys/types from schema
            keys = [f.get('key') for f in fields]
            types = [f.get('type') for f in fields]
            text_vals = [formData.get(k, '') for k in keys]
            num_vals = [formData.get(k, None) for k in keys]
            dd_vals = [formData.get(k, '') for k in keys]
            # Run validation
            res = inspector_save_handler(f'cards/{uuid}.md', keys, types, text_vals, num_vals, dd_vals)
            # res is a tuple: (toast, global_err_or_empty, *row_errors)
            toast = res[0]
            global_err = res[1] if len(res) > 1 else ''
            row_errs = list(res[2:]) if len(res) > 2 else []
            # Build a response payload for client helper
            # Build structured per-field error objects: { key: [ {path, message, code} ] }
            rowErrMap = {}
            firstInvalid = None
            for i,k in enumerate(keys):
                if i < len(row_errs) and row_errs[i]:
                    # Map string error to structured object
                    msg = row_errs[i]
                    code = 'REQUIRED' if 'required' in (msg or '').lower() else 'INVALID'
                    err_obj = {'path': f'fields.{k}', 'message': msg, 'code': code}
                    rowErrMap[k] = [err_obj]
                    if not firstInvalid:
                        firstInvalid = k
            payload_resp = {'ok': (global_err == '' or global_err is None), 'message': (('Saved' in toast) and 'Saved' or (global_err or 'Validation failed')), 'rowErrors': rowErrMap, 'firstInvalidKey': firstInvalid}
            # Trace dynamic save payload events for E2E
            try:
                from pathlib import Path
                Path('world_db').mkdir(parents=True, exist_ok=True)
                p = Path('world_db') / '.trace'
                p.write_text((p.read_text(encoding='utf-8') if p.exists() else '') + f"DYN_SAVE {uuid} {payload_resp.get('firstInvalidKey')} {time.time()}\n", encoding='utf-8')
            except Exception:
                pass
            # return toast plus a small script that calls the client-side handler
            import json as _json
            script = f"<script>try{{ if(window.handleDynamicSaveResponse) window.handleDynamicSaveResponse({_json.dumps(payload_resp)}); }}catch(e){{console.warn('dyn save resp err',e);}}</script>"
            # Append script to toast to execute on client
            if isinstance(toast, str):
                toast = toast + script
            else:
                toast = show_toast(payload_resp.get('message',''), 'info') + script
            return toast, gr.update(), gr.update(), gr.update(value='dynamic_save')
        except Exception as e:
            return show_toast(f'Error saving dynamic form: {e}','error'), gr.update(), gr.update(), gr.update(value='dynamic_save_error')

    if act == 'duplicate_card':
        cid = payload.get('uuid')
        toast, new_uuid = wb.duplicate_card_uuid(cid)
        return toast, gr.update(), gr.update(), gr.update(value='card_duplicated:' + (new_uuid or ''))

    if act in ('switch_to_textbox_auto', 'switch_to_textbox'):
        content = payload.get('content', '')
        status_val = 'autofallback' if act == 'switch_to_textbox_auto' else 'wrapped'
        return show_toast('Switched to wrapped textbox', 'info'), gr.update(visible=False), gr.update(value=content, visible=True), gr.update(value=status_val)

    if act == 'save_card_form':
        uuid = payload.get('uuid')
        formData = payload.get('formData', {})
        try:
            ok = wb.save_card_form_fields(uuid, formData)
            return show_toast('Saved form', 'info') if ok else show_toast('Save failed', 'error'), gr.update(), gr.update(), gr.update(value='form_saved:' + (uuid or ''))
        except Exception as e:
            return show_toast(f'Error saving form: {e}', 'error'), gr.update(), gr.update(), gr.update(value='form_save_error')

    if act == 'switch_to_code':
        content = payload.get('content', '')
        return show_toast('Switched to Code editor', 'info'), gr.update(value=content, visible=True), gr.update(visible=False), gr.update(value='editor')

    if act == 'wrap_status':
        st = payload.get('status','unknown')
        return show_toast(f'Wrap status: {st}', 'info' if st=='ok' else 'warn'), gr.update(), gr.update(), gr.update(value=st)

    return default


# Tree action wrapper for the UI
def on_tree_action(action_json: str):
    """Wrapper that handles tree-originating actions and returns outputs:
       (world_tree_text, status_text, editor_update_value, context_html)

    This is wired to the `tree_action_box` change event. It returns the refreshed
    tree string and (optionally) an updated editor content and context banner when
    the action requires opening an entry (e.g., after creating a card).
    """
    try:
        import src.tree_explorer as tree_explorer
    except Exception:
        return get_world_tree(), show_toast('Tree support not available','warn'), gr.update(), gr.update()
    toast, meta = tree_explorer.handle_tree_action_json(action_json)
    # If an operation suggests a tree update, refresh the tree string
    tree_str = get_world_tree()

    # Default outputs: update tree, show toast, no editor changes, no context change
    editor_out = gr.update()
    ctx_out = gr.update()

    # If a card was created or a card UUID is provided, open it in editor
    new_uuid = None
    focus = None
    if isinstance(meta, dict):
        new_uuid = meta.get('new_uuid') or meta.get('opened_uuid')
        focus = meta.get('focus')
        # If tree_explorer returned an 'opened' path, extract UUID from it for inspector rendering
        opened = meta.get('opened')
        if not new_uuid and isinstance(opened, str) and opened.startswith('cards/'):
            try:
                import re
                m = re.search(r"([0-9a-fA-F\-]{36})", opened)
                if m:
                    new_uuid = m.group(1)
            except Exception:
                new_uuid = None

    if not new_uuid and isinstance(focus, str) and focus.startswith('cards/'):
        # Attempt to extract UUID from focus string like 'cards/<uuid>.md'
        try:
            import re
            m = re.search(r"([0-9a-fA-F\-]{36})", focus)
            if m:
                new_uuid = m.group(1)
        except Exception:
            new_uuid = None

    inspector_html_out = ''
    if new_uuid:
        try:
            import src.world_builder as wb
            content, ctx_html = wb.open_card(new_uuid)
            # Render inspector fields if schema available
            try:
                fields = wb.get_card_form_fields(new_uuid)
                inspector_html_out = _render_inspector_html_for_card(new_uuid, fields) if fields is not None else "<div style='color:#666'>No schema associated with this card.</div>"
            except Exception:
                inspector_html_out = ""
            if content is not None:
                editor_out = gr.update(value=content)
                ctx_out = ctx_html
        except Exception:
            # If opening fails, don't block the tree refresh; set a placeholder content and show toast
            editor_out = gr.update(value=f"# New card: {new_uuid}")
            ctx_out = f"<div style='color:#ef4444'>Unable to open created card {new_uuid}</div>"

    # If server suggests the UI should focus a tree entry, append a small script to the toast to call focusTreeItem
    if focus:
        # Create a script snippet that will call the client-side helper
        import json as _json
        script = f"<script>try{{ if(window.focusTreeItem) window.focusTreeItem({_json.dumps(focus)}); }}catch(e){{console.warn('focus err',e);}}</script>"
        # Additionally instruct the client to open the created card (helps E2E determinism)
        open_script = ''
        try:
            if new_uuid:
                open_script = "<script>try{ setTimeout(function(){ try{ if(window.wbActionCallback) window.wbActionCallback(JSON.stringify({'action':'open','path':'cards/" + str(new_uuid) + "'})); }catch(e){console.warn('open intent err',e);} }, 150); }catch(e){console.warn('open intent err',e);}</script>"
        except Exception:
            open_script = ''
        # trace focus and open intent for E2E
        try:
            from pathlib import Path
            Path('world_db').mkdir(parents=True, exist_ok=True)
            p = Path('world_db') / '.trace'
            p.write_text((p.read_text(encoding='utf-8') if p.exists() else '') + f"FOCUS_INTENT {focus} {time.time()}\n", encoding='utf-8')
            if open_script:
                p.write_text((p.read_text(encoding='utf-8') if p.exists() else '') + f"OPEN_INTENT {new_uuid} {time.time()}\n", encoding='utf-8')
            # Test-only: if handshake enabled, write INSPECTOR_READY trace and append a small script to DOM to signal readiness
            import os as _os
            if _os.environ.get('WB_E2E_HANDSHAKE'):
                p.write_text((p.read_text(encoding='utf-8') if p.exists() else '') + f"INSPECTOR_READY {new_uuid} {time.time()}\n", encoding='utf-8')
        except Exception:
            pass

        # Test-only handshake script (appended if WB_E2E_HANDSHAKE is set)
        handshake_script = ''
        try:
            import os as _os
            import json as _json
            if _os.environ.get('WB_E2E_HANDSHAKE') and new_uuid:
                # set window.__wb_inspector_ready and emit an event for the test harness
                handshake_script = f"<script>try{{ window.__wb_inspector_ready = {_json.dumps(new_uuid)}; window.dispatchEvent(new CustomEvent('wb:inspector_ready', {{detail: {{uuid: {_json.dumps(new_uuid)} }} }})); }}catch(e){{console.warn('handshake err',e);}}</script>"
        except Exception:
            handshake_script = ''

        # If toast is an HTML snippet, append the script(s)
        if isinstance(toast, str):
            toast = toast + script + open_script + handshake_script
        else:
            toast = f"<script>showWBToast('Action complete','info');</script>" + script + open_script + handshake_script

    # Trace inspector set event for E2E/debugging
    try:
        if inspector_html_out and new_uuid:
            from pathlib import Path
            Path('world_db').mkdir(parents=True, exist_ok=True)
            p = Path('world_db') / '.trace'
            p.write_text((p.read_text(encoding='utf-8') if p.exists() else '') + f"INSPECTOR_SET {new_uuid} {time.time()}\n", encoding='utf-8')
    except Exception:
        pass

    return tree_str, toast, editor_out, ctx_out, inspector_html_out


# Module-level helpers for confirm modal logic (extracted so they are unit-testable)
def handle_confirm_save(pending_payload_json: str):
    """Process a pending save_new_version confirmation payload.

    Returns the same tuple shape as the original `_on_confirm_yes` handler used in the app.
    """
    try:
        payload = json.loads(pending_payload_json or '{}')
    except Exception:
        payload = {}
    if not payload or payload.get('action') != 'save_new_version':
        # nothing to do
        return show_toast('Nothing to confirm','warn'), {'choices': [], 'value': None}, gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), ''
    rel = payload.get('rel')
    content = payload.get('content')
    notes = payload.get('notes')
    res = wb.save_new_version(rel, content, notes=notes)
    toast_html_out = show_toast(str(res), 'info')
    versions = wb.list_versions(rel) if rel else []
    versions_update = {'choices': versions, 'value': (versions[0] if versions else None)}
    # Hide modal and clear pending
    return toast_html_out, versions_update, gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), ''


def handle_confirm_cancel(_pending: str):
    """Cancel pending confirmation and hide modal."""
    return show_toast('Cancelled', 'info'), {'choices': [], 'value': None}, gr.update(visible=False), gr.update(visible=False), ''


def handle_debounce_change(val):
    try:
        res = wb.set_debounce(val)
        # wb.set_debounce returns script HTML; return as safe toast snippet
        if isinstance(res, str) and res.strip().startswith('<script>'):
            return res
        return show_toast(str(res), 'info')
    except Exception as e:
        return show_toast(f'Error setting debounce: {e}','error')


def handle_auto_refresh_toggle(enabled: bool):
    return show_toast('Auto-refresh enabled' if enabled else 'Auto-refresh disabled', 'info')


def create_app():
    with gr.Blocks(title="World Builder — Minimal UI") as app:
        # inject toast script, CSS and helpers
        gr.HTML(APP_STYLE)
        
        with gr.Tabs() as main_tabs:
            # --- GENERATE MODE ---
            with gr.Tab("Generate", id="tab_generate"):
                gr.HTML("<div style='color:#0f1724;background:#eef2ff;border-left:4px solid #4f46e5;padding:10px;margin-bottom:10px;'><strong style='color:#0f1724'>Mode: Generate</strong> — Create candidate content. Nothing is saved to canon unless explicitly promoted.</div>")
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 📜 Scripts")
                        # Populate scripts from the workspace 'Narrative Scripts/' folder
                        from pathlib import Path
                        prompt_root = Path.cwd() / "Narrative Scripts"

                        def _gather_top_categories():
                            if not prompt_root.exists():
                                return []
                            return sorted([p.name for p in prompt_root.iterdir() if p.is_dir()])

                        def _gather_subcategories(top_cat):
                            if not prompt_root.exists():
                                return []
                            if not top_cat or top_cat == 'All':
                                return []
                            base = prompt_root / top_cat
                            if not base.exists():
                                return []
                            return sorted([p.name for p in base.iterdir() if p.is_dir()])

                        def _list_scripts(top_cat=None, sub_cat=None):
                            scripts = []
                            if not prompt_root.exists():
                                return scripts
                            # Resolve base path according to selection
                            if not top_cat or top_cat == 'All':
                                base = prompt_root
                            else:
                                base = prompt_root / top_cat
                            if sub_cat and sub_cat != '(All)':
                                base = base / sub_cat
                            if not base.exists():
                                return scripts
                            for p in base.rglob("*"):
                                if p.is_file() and p.suffix.lower() in (".md", ".txt"):
                                    scripts.append(p.relative_to(prompt_root).as_posix())
                            scripts.sort()
                            return scripts

                        # Handlers to update subcategory list and scripts list
                        def _on_category_change(cat):
                            subs = _gather_subcategories(cat)
                            sub_choices = ['(All)'] + subs if subs else []
                            scripts = _list_scripts(top_cat=(None if cat == 'All' else cat))
                            return (
                                gr.update(choices=sub_choices, value='(All)' if sub_choices else None, visible=bool(sub_choices)),
                                gr.update(choices=scripts, value=(scripts[0] if scripts else None))
                            )

                        def _on_subcategory_change(sub, cat):
                            scripts = _list_scripts(top_cat=(None if cat == 'All' else cat), sub_cat=(None if not sub or sub == '(All)' else sub))
                            return gr.update(choices=scripts, value=(scripts[0] if scripts else None))

                        # Initial population
                        top_cats = _gather_top_categories()
                        categories = ['All'] + top_cats if top_cats else ['All']
                        initial_cat = categories[0] if categories else 'All'
                        initial_subs = _gather_subcategories(initial_cat)
                        subcat_dd = gr.Dropdown(choices=(['(All)'] + initial_subs if initial_subs else []), value='(All)' if initial_subs else None, label="Subcategory", visible=bool(initial_subs))
                        category_dd = gr.Dropdown(choices=categories, value=initial_cat, label="Category")
                        # Scripts selection (Category -> Subcategory -> Script)
                        script_selector = gr.Dropdown(choices=_list_scripts(initial_cat, None), label="Select Script")

                        # Wire changes: update subcategories and scripts when category changes; update scripts when subcategory changes
                        category_dd.change(_on_category_change, inputs=[category_dd], outputs=[subcat_dd, script_selector])
                        subcat_dd.change(_on_subcategory_change, inputs=[subcat_dd, category_dd], outputs=[script_selector])
                        # Execution controls (Model, Temperature, Sync, Run)
                        gr.Markdown('### 🧠 Execution')
                        model_dd = gr.Dropdown(choices=['mistral:latest','llama3:8b','deepseek-r1:7b'], value='mistral:latest', label='Model')
                        temp = gr.Slider(0.0, 1.5, value=0.7, step=0.05, label='Temperature')
                        sync_models_btn = gr.Button('🔄 Sync Models', size='sm')
                        run_btn = gr.Button('▶ RUN MODEL', variant='primary', size='lg')
                        
                    with gr.Column(scale=2):
                        gr.Markdown("### 🧠 Prompt & Output")
                        prompt_editor = gr.Code(language='markdown', lines=10, interactive=True, label="Prompt Editor", elem_id='wb-editor')
                        # Fallback wrapped textbox (hidden by default). Will be shown if wrapping cannot be enabled in CodeMirror.
                        prompt_editor_text = gr.Textbox('', lines=10, interactive=True, label="Prompt Editor (Wrapped)", visible=False, elem_id='wb-editor-textbox')
                        model_output = gr.Code(language='markdown', lines=15, interactive=False, label="Model Output (Read-only)")
                        # Execution telemetry / status is separate from the model output.
                        # `model_output` must only contain model text. `status_html` owns errors, timing, retries.
                        status_html = gr.HTML('', label='Execution Status')
                        # Wrap detection / status for debugging and auto-fallback
                        wrap_status_html = gr.HTML('', label='Wrap Status')
                        with gr.Row():
                            promote_btn = gr.Button("📥 Promote to World Database")
                            clear_gen_btn = gr.Button("🗑 Clear")
                            switch_to_textbox_btn = gr.Button('Use Wrapped Textbox', size='sm')
                            switch_to_code_btn = gr.Button('Use Code Editor', size='sm', visible=False)
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 📖 World Database Preview (Read-only)")
                        world_preview = gr.Code(language='markdown', interactive=False, lines=10, label="Reference Content")

            # --- WORLD EDITOR MODE ---
            with gr.Tab("World Editor", id="tab_editor"):
                gr.HTML("<div style='color:#0f1724;background:#f0fdf4;border-left:4px solid #22c55e;padding:10px;margin-bottom:10px;'><strong style='color:#0f1724'>Mode: World Editor</strong> — Maintain canonical truth. Explicit actions and versioned.</div>")
                with gr.Row():
                    with gr.Column(scale=1, min_width=260):
                        gr.Markdown("### 📚 World Database")
                        # Use the new tree_explorer component which provides a tree view and an action bridge
                        import src.tree_explorer as tree_explorer
                        world_tree, tree_action_box = tree_explorer.build_tree_component()
                        file_select = gr.Dropdown(choices=get_world_files(), value=(get_world_files()[0] if get_world_files() else None), label='Select Entry')
                        refresh_btn = gr.Button('🔄 Refresh')
                        # time/status element used as one of the change outputs
                        last_refreshed = gr.HTML('Last refreshed: Never')
                        # Wire the tree action textbox to `on_tree_action` which returns (updated_tree, toast_html, editor_update, ctx_html)
                        try:
                            tree_action_box.change(on_tree_action, inputs=[tree_action_box], outputs=[world_tree, last_refreshed, editor, context_banner, inspector_html])
                        except Exception:
                            # If certain components (like `editor`) are not yet defined in some test harnesses, fail gracefully.
                            try:
                                tree_action_box.change(on_tree_action, inputs=[tree_action_box], outputs=[world_tree, last_refreshed, gr.update(), context_banner, inspector_html])
                            except Exception:
                                pass
                        # Left column action stubs (download/copy)
                        with gr.Row():
                            download_btn = gr.Button('⬇ Download', size='sm')
                            copy_btn = gr.Button('📋 Copy', size='sm')
                        
                        # Auto-refresh control and debounce
                        auto_refresh = gr.Checkbox(label='Auto-refresh tree', value=True)
                        debounce_slider = gr.Slider(0.1, 5.0, value=wb.DEBOUNCE_SECONDS, step=0.1, label='Debounce (s)')

                    with gr.Column(scale=2):
                        context_banner = gr.HTML("<div style='color:#0f1724;background:#f0f0f0;border-left:4px solid #666;padding:10px 14px;font-family:system-ui;'><strong>📌 Context:</strong> World Editor<br><strong>Path:</strong> (none)<br><strong>State:</strong> <span style='color:green;'>✅ Clean</span></div>", visible=True)
                        # Inspector container: dynamic HTML renderer (preferred) + legacy per-field components for progressive enhancement
                        inspector_html = gr.HTML('<div style="color:#666">Inspector: select a card to edit fields</div>', visible=True, label='Inspector')
                        # Legacy per-field components (kept for compatibility; will be hidden when dynamic renderer active)
                        inspector_key_states = []
                        inspector_type_states = []
                        inspector_title_htmls = []
                        inspector_text_inputs = []
                        inspector_num_inputs = []
                        inspector_dropdowns = []
                        inspector_row_errors = []
                        # create rows
                        for i in range(MAX_INSPECTOR_FIELDS):
                            inspector_key_states.append(gr.State(''))
                            inspector_type_states.append(gr.State(''))
                            inspector_title_htmls.append(gr.HTML('', visible=False))
                            inspector_text_inputs.append(gr.Textbox('', visible=False, label=f'Value {i}'))
                            inspector_num_inputs.append(gr.Number(value=None, visible=False, label=f'Value (num) {i}'))
                            inspector_dropdowns.append(gr.Dropdown(choices=[], value=None, visible=False, label=f'Value (select) {i}'))
                            inspector_row_errors.append(gr.HTML('', visible=False))
                        inspector_save_btn = gr.Button('Save Form', size='sm')
                        with gr.Row():
                            gutter_html = gr.HTML("<div id='wb-gutter' class='wb-gutter' style='height:320px;overflow:auto;'><div id='wb-gutter-lines'></div></div>")
                            editor = gr.Code(language='markdown', lines=20, interactive=True, elem_id='wb-editor')
                        
                        original_content = gr.State('')
                        is_dirty = gr.State(False)
                        
                        with gr.Row():
                            save_btn = gr.Button('💾 Save', variant='primary')
                            revert_btn = gr.Button('↩ Revert')
                            restore_as_canon_btn = gr.Button('📥 Restore as New Canon Version', variant='primary', visible=False)
                        
                        with gr.Accordion("Versioning & Drafts", open=False) as versioning_accordion:
                            with gr.Row():
                                versions_dd = gr.Dropdown(choices=[], value=None, label='Versions')
                                load_version_btn = gr.Button('📂 Load Version')
                            with gr.Row():
                                version_notes = gr.Textbox('', label='Notes', placeholder='Short description for this version')
                                save_version_btn = gr.Button('🕘 Save as New Version')
                            with gr.Row():
                                restore_draft_btn = gr.Button('🔄 Restore Draft')

                        with gr.Accordion("AI Assist (Scoped)", open=False) as ai_assist_accordion:
                            with gr.Row():
                                assist_shorten = gr.Button('Shorten')
                                assist_expand = gr.Button('Expand')
                                assist_refactor = gr.Button('Refactor')
                                assist_context = gr.Button('Contextual')
                            assist_output = gr.Code('', language='markdown', lines=8, interactive=False)

                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown('### Activity')
                        activity_html = gr.HTML(wb.get_activity_log_html(), label='Activity Log')

        # --- GLOBAL COMPONENTS (Hidden) ---
        toast_html = gr.HTML('', visible=True)
        wb_action_box = gr.Textbox('', visible=False, elem_id='wb-action-box')
        pending_action = gr.State('')
        # Execution running flag: single source of truth for model execution state
        is_running = gr.State(False)
        
        # --- WIRING ---

        # Generate Mode Wiring
        def _on_script_select(name):
            from .ollama_runner import read_prompt, NARRATIVE_DIR
            try:
                path = os.path.join(NARRATIVE_DIR, name)
                return read_prompt(path)
            except Exception as e:
                return f"Error loading script: {e}"

        script_selector.change(_on_script_select, inputs=[script_selector], outputs=[prompt_editor])
        
        def _sync_models():
          """Query Ollama for available models and update the model dropdown."""
          try:
            from .ollama_runner import list_models_cli, load_models_from_cache
            models = []
            try:
              models = list_models_cli() or []
            except Exception:
              models = []
            if not models:
              try:
                models = load_models_from_cache() or []
              except Exception:
                models = []
            # normalize to strings
            models = [str(m) for m in models]
            if not models:
              return gr.update(choices=[], value=None), show_toast('No models found (check Ollama)', 'warn')
            return gr.update(choices=models, value=(models[0] if models else None)), show_toast('Models synced', 'info')
          except Exception as e:
            return gr.update(choices=[], value=None), show_toast(f'Error syncing models: {e}', 'error')

        sync_models_btn.click(_sync_models, inputs=[], outputs=[model_dd, toast_html])
        # CRITICAL: run_btn outputs ONLY model_output. Status and is_running are not execution outputs.
        # This prevents Gradio from binding multiple components to the same long-running task.
        run_btn.click(run_model, inputs=[prompt_editor, model_dd, temp, is_running], outputs=[model_output])
        
        def _on_promote(output):
            if not output or not str(output).strip():
                return show_toast("Nothing to promote", "warn"), gr.update(value=get_world_tree()), gr.update(choices=get_world_files(), value=(get_world_files()[0] if get_world_files() else None)), f"Last refreshed: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            try:
                # Construct a safe filename from the first non-empty line or use timestamp
                first_line = ''
                for line in str(output).splitlines():
                    if line.strip():
                        first_line = line.strip(); break
                name_base = first_line or f"promoted_{int(time.time())}"
                # sanitize
                import re
                safe = re.sub(r"[^0-9A-Za-z_-]", "", name_base.replace(' ', '_'))[:40] or f"promoted_{int(time.time())}"
                dir_path = os.path.join('world_db', 'promoted')
                os.makedirs(dir_path, exist_ok=True)
                target = os.path.join(dir_path, safe + '.md')
                # ensure uniqueness
                suffix = 1
                while os.path.exists(target):
                    target = os.path.join(dir_path, f"{safe}_{suffix}.md")
                    suffix += 1
                with open(target, 'w', encoding='utf-8') as fh:
                    fh.write(str(output))
                try:
                    Path('world_db/.last_mod').write_text(str(time.time()))
                except Exception:
                    pass
                # Refresh tree and files
                tree, files_upd = refresh_tree_ui()
                ts = f"Last refreshed: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                toast = show_toast(f"Promoted to {target}", 'info')
                return toast, tree, files_upd, ts
            except Exception as e:
                return show_toast(f"Promotion failed: {e}", 'error'), gr.update(value=get_world_tree()), gr.update(choices=get_world_files(), value=(get_world_files()[0] if get_world_files() else None)), f"Last refreshed: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        promote_btn.click(_on_promote, inputs=[model_output], outputs=[toast_html, world_tree, file_select, last_refreshed])
        clear_gen_btn.click(lambda: ("", ""), outputs=[prompt_editor, model_output])

        # Editor Mode Wiring
        def _on_refresh():
            tree, files_upd = refresh_tree_ui()
            ts = f"Last refreshed: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            return tree, files_upd, ts

        refresh_btn.click(_on_refresh, inputs=[], outputs=[world_tree, file_select, last_refreshed])
        
        # _render_inspector_html_for_card moved to module level for reuse and testing

        def _on_select(relpath):
            if not relpath:
                return "", "", "", False, gr.update(visible=True), gr.update(choices=[], value=None), gr.update(interactive=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=False), ""

            content, activity = load_file(relpath)
            is_version = relpath.startswith('.versions/')

            # If the file selected is a card under cards/, attempt to render inspector
            inspector_content = ""
            if relpath.startswith('cards/'):
                # extract uuid
                import re
                m = re.search(r"([0-9a-fA-F\-]{36})", relpath)
                if m:
                    uuid = m.group(1)
                    try:
                        fields = wb.get_card_form_fields(uuid)
                        inspector_content = _render_inspector_html_for_card(uuid, fields) if fields is not None else "<div style='color:#666'>No schema associated with this card.</div>"
                    except Exception:
                        inspector_content = "<div style='color:#ef4444'>Error loading inspector</div>"

            if is_version:
                banner = f"<div style='color:#0f1724;background:#fffbeb;border-left:4px solid #d97706;padding:10px 14px;font-family:system-ui;'><strong>📌 Context:</strong> Historical Version<br><strong>Path:</strong> {relpath}<br><strong>State:</strong> <span style='color:#d97706;'>🔒 Read-only snapshot</span></div>"
                return (
                    content, activity, content, False, banner, 
                    gr.update(choices=[], value=None), 
                    gr.update(interactive=False), 
                    gr.update(visible=False), 
                    gr.update(visible=False), 
                    gr.update(visible=False), 
                    gr.update(visible=False), 
                    gr.update(visible=True),
                    inspector_content
                )
            else:
                banner = f"<div style='color:#0f1724;background:#f0fdf4;border-left:4px solid #22c55e;padding:10px 14px;font-family:system-ui;'><strong>📌 Context:</strong> Canonical File<br><strong>Path:</strong> {relpath}<br><strong>State:</strong> <span style='color:green;'>✅ Clean</span></div>"
                versions = wb.list_versions(relpath) if relpath else []
                versions_update = gr.update(choices=versions, value=(versions[0] if versions else None))

                # If the selected entry is a card, prepare the per-row component updates
                comp_updates = []
                if relpath.startswith('cards/'):
                    import re
                    m = re.search(r"([0-9a-fA-F\-]{36})", relpath)
                    if m:
                        uuid = m.group(1)
                        fields = wb.get_card_form_fields(uuid)
                        rows = build_inspector_rows(fields) if fields is not None else []
                        # populate component updates for up to MAX_INSPECTOR_FIELDS
                        # Also build dynamic HTML for the inspector and set it into inspector_html
                        inspector_html_val = []
                        for i in range(MAX_INSPECTOR_FIELDS):
                            if i < len(rows):
                                # support optional enum at index 5
                                if len(rows[i]) == 6:
                                    key, title, ftype, val, required, enum = rows[i]
                                else:
                                    key, title, ftype, val, required = rows[i]
                                    enum = None
                                # key and type states
                                comp_updates.append(gr.update(value=key))
                                comp_updates.append(gr.update(value=ftype))
                                comp_updates.append(gr.update(value=f"<div style='font-weight:700'>{title}{' *' if required else ''}</div>", visible=True))
                                if enum:
                                    comp_updates.append(gr.update(visible=False))
                                    comp_updates.append(gr.update(visible=False))
                                    comp_updates.append(gr.update(choices=list(enum), value=val, visible=True))
                                elif ftype in ('integer','number'):
                                    comp_updates.append(gr.update(value=int(val) if str(val).strip()!='' else None, visible=True))
                                    comp_updates.append(gr.update(visible=False))
                                    comp_updates.append(gr.update(visible=False))
                                else:
                                    comp_updates.append(gr.update(visible=False))
                                    comp_updates.append(gr.update(value=str(val), visible=True))
                                    comp_updates.append(gr.update(visible=False))
                                comp_updates.append(gr.update(value='', visible=False))
                                inspector_html_val.append(_render_inspector_html_for_card(uuid, rows[:len(rows)]))
                            else:
                                # clear the rest
                                comp_updates.append(gr.update(value=''))
                                comp_updates.append(gr.update(value=''))
                                comp_updates.append(gr.update(value='', visible=False))
                                comp_updates.append(gr.update(visible=False))
                                comp_updates.append(gr.update(visible=False))
                                comp_updates.append(gr.update(value='', visible=False))
                        # if dynamic html built, set first instance
                        if inspector_html_val:
                            comp_updates.append(gr.update(value=inspector_html_val[0]))
                        else:
                            comp_updates.append(gr.update(value="<div style='color:#666'>Inspector: no fields</div>"))

                # Build return tuple: default outputs plus all component updates
                return (
                    content, activity, content, False, banner, 
                    versions_update, 
                    gr.update(interactive=True), 
                    gr.update(visible=True), 
                    gr.update(visible=True), 
                    gr.update(visible=True), 
                    gr.update(visible=True), 
                    gr.update(visible=False),
                    *comp_updates
                )

        def _on_editor_change(new_content, original, relpath):
            if not relpath or relpath.startswith('.versions/'):
                return gr.update(visible=True), False, gr.update(visible=False), gr.update(visible=False)
            dirty = (new_content != original)
            state_color = "#ff8c00" if dirty else "green"
            state_text = "⚠️ Modified (unsaved)" if dirty else "✅ Clean"
            banner = f"<div style='color:#0f1724;background:#f0f0f0;border-left:4px solid #666;padding:10px 14px;font-family:system-ui;'><strong>📌 Context:</strong> World Editor<br><strong>Path:</strong> {relpath}<br><strong>State:</strong> <span style='color:{state_color};'>{state_text}</span></div>"
            return banner, dirty, gr.update(visible=True), gr.update(visible=dirty)

        editor.change(_on_editor_change, inputs=[editor, original_content, file_select], outputs=[context_banner, is_dirty, save_btn, revert_btn])

        def _on_save(relpath, content):
            toast, out_content, tree_text, activity = save_file(relpath, content)
            toast_html_out = toast if (isinstance(toast, str) and toast.strip().startswith('<script>')) else show_toast(str(toast or 'Saved'), 'info')
            banner = f"<div style='color:#0f1724;background:#f0fdf4;border-left:4px solid #22c55e;padding:10px 14px;font-family:system-ui;'><strong style='color:#0f1724'>📌 Context:</strong> Canonical File<br><strong style='color:#0f1724'>Path:</strong> {relpath}<br><strong style='color:#0f1724'>State:</strong> <span style='color:green;'>✅ Clean (saved)</span></div>"
            versions = wb.list_versions(relpath) if relpath else []
            versions_update = gr.update(choices=versions, value=(versions[0] if versions else None))
            return toast_html_out, out_content, tree_text, activity, out_content, False, banner, versions_update, gr.update(visible=False)

        save_btn.click(_on_save, inputs=[file_select, editor], outputs=[toast_html, editor, world_tree, activity_html, original_content, is_dirty, context_banner, versions_dd, revert_btn])
        
        def _on_revert(original, relpath):
            banner = f"<div style='color:#0f1724;background:#f0fdf4;border-left:4px solid #22c55e;padding:10px 14px;font-family:system-ui;'><strong style='color:#0f1724'>📌 Context:</strong> Canonical File<br><strong style='color:#0f1724'>Path:</strong> {relpath}<br><strong style='color:#0f1724'>State:</strong> <span style='color:green;'>✅ Clean (reverted)</span></div>"
            return original, banner, False, gr.update(visible=False)

        def _on_load_version(relpath, version_id):
            if not version_id:
                return '', f"<div style='color:#0f1724;background:#f0f0f0;border-left:4px solid #666;padding:10px 14px;font-family:system-ui;'><strong>📌 Context:</strong> World Editor<br><strong>Path:</strong> {relpath}<br><strong>State:</strong> <span style='color:red;'>❌ No version selected</span></div>", False, '', gr.update(visible=False)
            content = wb.load_version(relpath, version_id)
            banner = f"<div style='color:#0f1724;background:#f0fdf4;border-left:4px solid #22c55e;padding:10px 14px;font-family:system-ui;'><strong>📌 Context:</strong> Canonical File<br><strong>Path:</strong> {relpath}<br><strong>State:</strong> <span style='color:green;'>✅ Loaded version: {version_id}</span></div>"
            return content or '', banner, False, content or '', gr.update(visible=False)


        def _on_restore_draft(relpath):
            draft = wb.restore_draft(relpath)
            if not draft:
                return '', f"<div style='color:#0f1724;background:#f0f0f0;border-left:4px solid #666;padding:10px 14px;font-family:system-ui;'><strong>📌 Context:</strong> World Editor<br><strong>Path:</strong> {relpath}<br><strong>State:</strong> <span style='color:red;'>❌ No draft found</span></div>", False, gr.update(visible=False)
            banner = f"<div style='color:#0f1724;background:#f0f0f0;border-left:4px solid #666;padding:10px 14px;font-family:system-ui;'><strong>📌 Context:</strong> World Editor<br><strong>Path:</strong> {relpath}<br><strong>State:</strong> <span style='color:#ff8c00;'>⚠️ Draft restored (unsaved)</span></div>"
            return draft, banner, True, gr.update(visible=True)

        def _on_ai_assist(action, content, model, temperature):
            visible_update, suggestion, status = wb.ai_assist_action(action, content, model, temperature)
            toast = show_toast(status, 'info' if status.startswith('✅') else 'error')
            return suggestion, toast

        def _on_action(action_json):
            return handle_action_json(action_json)

        def _on_restore_as_canon(relpath, content):
            if not relpath or not relpath.startswith('.versions/'):
                return show_toast("Not a version file", "error"), gr.update(), gr.update()
            
            # Extract original filename from version path
            # .versions/path/to/file.md/v_timestamp.md -> path/to/file.md
            parts = relpath.split('/')
            if len(parts) < 3:
                return show_toast("Invalid version path", "error"), gr.update(), gr.update()
            
            canon_relpath = '/'.join(parts[1:-1])
            toast, out_content, tree_text, activity = save_file(canon_relpath, content)
            
            # Switch to the newly restored canon file
            return toast, canon_relpath, out_content

        revert_btn.click(_on_revert, inputs=[original_content, file_select], outputs=[editor, context_banner, is_dirty, revert_btn])
        restore_as_canon_btn.click(_on_restore_as_canon, inputs=[file_select, editor], outputs=[toast_html, file_select, editor])
        
        save_version_btn.click(lambda rel, content, notes: wb.save_new_version(rel, content, notes=notes), inputs=[file_select, editor, version_notes], outputs=[toast_html, versions_dd])
        load_version_btn.click(_on_load_version, inputs=[file_select, versions_dd], outputs=[editor, context_banner, is_dirty, original_content, revert_btn])
        restore_draft_btn.click(_on_restore_draft, inputs=[file_select], outputs=[editor, context_banner, is_dirty, revert_btn])
        
        assist_shorten.click(lambda *_: _on_ai_assist('Shorten', editor.value if hasattr(editor, 'value') else '', model_dd.value, temp.value), inputs=[], outputs=[assist_output, toast_html])
        assist_expand.click(lambda *_: _on_ai_assist('Expand', editor.value if hasattr(editor, 'value') else '', model_dd.value, temp.value), inputs=[], outputs=[assist_output, toast_html])
        assist_refactor.click(lambda *_: _on_ai_assist('Refactor', editor.value if hasattr(editor, 'value') else '', model_dd.value, temp.value), inputs=[], outputs=[assist_output, toast_html])
        assist_context.click(lambda *_: _on_ai_assist('Contextual', editor.value if hasattr(editor, 'value') else '', model_dd.value, temp.value), inputs=[], outputs=[assist_output, toast_html])

        # When a script is selected in Generate tab, load its content into the Prompt Editor
        try:
          script_selector.change(_on_script_select, inputs=[script_selector], outputs=[prompt_editor])
        except Exception:
          # best-effort wiring; if components not in scope, ignore
          pass

        wb_action_box.change(_on_action, inputs=[wb_action_box], outputs=[toast_html, prompt_editor, prompt_editor_text, wrap_status_html])

        # Inspector: Save button wiring
        def _on_inspector_save(relpath, *components):
            # components: keys(MAX), types(MAX), text_vals(MAX), num_vals(MAX), dd_vals(MAX)
            try:
                k = 0
                keys = list(components[k:k+MAX_INSPECTOR_FIELDS]); k += MAX_INSPECTOR_FIELDS
                types = list(components[k:k+MAX_INSPECTOR_FIELDS]); k += MAX_INSPECTOR_FIELDS
                text_vals = list(components[k:k+MAX_INSPECTOR_FIELDS]); k += MAX_INSPECTOR_FIELDS
                num_vals = list(components[k:k+MAX_INSPECTOR_FIELDS]); k += MAX_INSPECTOR_FIELDS
                dd_vals = list(components[k:k+MAX_INSPECTOR_FIELDS])
            except Exception:
                return show_toast('Inspector save: bad inputs','error'), 'Invalid inputs'
            res = inspector_save_handler(relpath, keys, types, text_vals, num_vals, dd_vals)
            # res: (toast, global_err) or (toast, global_err, *row_errs)
            toast = res[0]
            global_err = res[1] if len(res) > 1 else ''
            row_errs = list(res[2:]) if len(res) > 2 else []
            # pad row_errs to MAX and return: (toast, global_err, *row_errs)
            padded = row_errs + [''] * (MAX_INSPECTOR_FIELDS - len(row_errs))
            return (toast, global_err, *padded)

        try:
            # Prepare inputs: file_select + keys + types + text + num + dropdowns
            inspector_inputs = [file_select]
            inspector_inputs += inspector_key_states + inspector_type_states + inspector_text_inputs + inspector_num_inputs + inspector_dropdowns
            # Outputs: toast_html, global error, then per-row error htmls
            inspector_outputs = [toast_html,]* (1) + [None,]* (1) + inspector_row_errors
            # The handler will return (toast, global_err, *row_errs)
            inspector_save_btn.click(_on_inspector_save, inputs=inspector_inputs, outputs=[toast_html, inspector_error_html] + inspector_row_errors)
        except Exception:
            # best-effort: if components not in scope, ignore
            pass
        
        def _switch_to_textbox(code_content):
            return gr.update(visible=False), gr.update(value=code_content, visible=True), show_toast('Switched to wrapped textbox', 'info')

        def _switch_to_code(text_value):
            return gr.update(value=text_value, visible=True), gr.update(visible=False), show_toast('Switched to Code editor', 'info')

        switch_to_textbox_btn.click(_switch_to_textbox, inputs=[prompt_editor], outputs=[prompt_editor, prompt_editor_text, toast_html])
        switch_to_code_btn.click(_switch_to_code, inputs=[prompt_editor_text], outputs=[prompt_editor, prompt_editor_text, toast_html])
        debounce_slider.change(handle_debounce_change, inputs=[debounce_slider], outputs=[toast_html])
        auto_refresh.change(handle_auto_refresh_toggle, inputs=[auto_refresh], outputs=[toast_html])

        # Auto-sync models when the page loads
        try:
          app.load(_sync_models, inputs=None, outputs=[model_dd, toast_html])
        except Exception:
          # If load wiring fails (older gradio), fall back to no-op
          pass

    return app



if __name__ == '__main__':
    app = create_app()
    app.launch()

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
from src.indexer import get_world_tree, get_world_files
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
.gradio-container .gr-code pre, .gradio-container .gr-code code, .gradio-container .gr-code textarea, .gradio-container .gr-code .cm-scroller { white-space: pre-wrap !important; overflow-wrap: anywhere !important; word-break: break-word !important; }
.CodeMirror, .CodeMirror * { white-space: pre-wrap !important; overflow-wrap: anywhere !important; word-break: break-word !important; }
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
    var el = document.getElementById('wb-action-box');
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

def run_model(prompt: str, model: str, temperature: float, is_running_state: bool):
    """Execute Ollama and return model output text only.

    This function returns ONLY the final text output. Gradio resolves immediately.
    Status, toasts, and execution state are NOT outputs of this function.
    """
    try:
        ok, payload = run_ollama_gen(prompt, model, temperature, timeout=120)
        if ok:
            out = payload.get('stdout', '')
            return out
        else:
            return ''
    except Exception:
        return ''


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

    if act in ('switch_to_textbox_auto', 'switch_to_textbox'):
        content = payload.get('content', '')
        status_val = 'autofallback' if act == 'switch_to_textbox_auto' else 'wrapped'
        return show_toast('Switched to wrapped textbox', 'info'), gr.update(visible=False), gr.update(value=content, visible=True), gr.update(value=status_val)

    if act == 'switch_to_code':
        content = payload.get('content', '')
        return show_toast('Switched to Code editor', 'info'), gr.update(value=content, visible=True), gr.update(visible=False), gr.update(value='editor')

    if act == 'wrap_status':
        st = payload.get('status','unknown')
        return show_toast(f'Wrap status: {st}', 'info' if st=='ok' else 'warn'), gr.update(), gr.update(), gr.update(value=st)

    return default


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
                gr.HTML("<div style='background:#eef2ff;border-left:4px solid #4f46e5;padding:10px;margin-bottom:10px;'><strong>Mode: Generate</strong> — Create candidate content. Nothing is saved to canon unless explicitly promoted.</div>")
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
                gr.HTML("<div style='background:#f0fdf4;border-left:4px solid #22c55e;padding:10px;margin-bottom:10px;'><strong>Mode: World Editor</strong> — Maintain canonical truth. Explicit actions and versioned.</div>")
                with gr.Row():
                    with gr.Column(scale=1, min_width=260):
                        gr.Markdown("### 📚 World Database")
                        world_tree = gr.Code(value=get_world_tree(), language='markdown', interactive=False, lines=20)
                        file_select = gr.Dropdown(choices=get_world_files(), value=(get_world_files()[0] if get_world_files() else None), label='Select Entry')
                        refresh_btn = gr.Button('🔄 Refresh')
                        # Left column action stubs (download/copy)
                        with gr.Row():
                            download_btn = gr.Button('⬇ Download', size='sm')
                            copy_btn = gr.Button('📋 Copy', size='sm')
                        
                        # Auto-refresh control and debounce
                        auto_refresh = gr.Checkbox(label='Auto-refresh tree', value=True)
                        debounce_slider = gr.Slider(0.1, 5.0, value=wb.DEBOUNCE_SECONDS, step=0.1, label='Debounce (s)')
                        last_refreshed = gr.HTML('Last refreshed: Never')

                    with gr.Column(scale=2):
                        context_banner = gr.HTML("<div style='background:#f0f0f0;border-left:4px solid #666;padding:10px 14px;font-family:system-ui;'><strong>📌 Context:</strong> World Editor<br><strong>Path:</strong> (none)<br><strong>State:</strong> <span style='color:green;'>✅ Clean</span></div>", visible=True)
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
            if not output:
                return show_toast("Nothing to promote", "warn")
            # In a real app, this might open a dialog to choose a filename
            return show_toast("Promotion dialog not yet implemented. Copy-paste to Editor for now.", "info")
        
        promote_btn.click(_on_promote, inputs=[model_output], outputs=[toast_html])
        clear_gen_btn.click(lambda: ("", ""), outputs=[prompt_editor, model_output])

        # Editor Mode Wiring
        def _on_refresh():
            tree, files_upd = refresh_tree_ui()
            ts = f"Last refreshed: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            return tree, files_upd, ts

        refresh_btn.click(_on_refresh, inputs=[], outputs=[world_tree, file_select, last_refreshed])
        
        def _on_select(relpath):
            if not relpath:
                return "", "", "", False, gr.update(visible=True), gr.update(choices=[], value=None), gr.update(interactive=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=False)
            
            content, activity = load_file(relpath)
            is_version = relpath.startswith('.versions/')
            
            if is_version:
                banner = f"<div style='background:#fffbeb;border-left:4px solid #d97706;padding:10px 14px;font-family:system-ui;'><strong>📌 Context:</strong> Historical Version<br><strong>Path:</strong> {relpath}<br><strong>State:</strong> <span style='color:#d97706;'>🔒 Read-only snapshot</span></div>"
                return (
                    content, activity, content, False, banner, 
                    gr.update(choices=[], value=None), 
                    gr.update(interactive=False), 
                    gr.update(visible=False), 
                    gr.update(visible=False), 
                    gr.update(visible=False), 
                    gr.update(visible=False), 
                    gr.update(visible=True)
                )
            else:
                banner = f"<div style='background:#f0fdf4;border-left:4px solid #22c55e;padding:10px 14px;font-family:system-ui;'><strong>📌 Context:</strong> Canonical File<br><strong>Path:</strong> {relpath}<br><strong>State:</strong> <span style='color:green;'>✅ Clean</span></div>"
                versions = wb.list_versions(relpath) if relpath else []
                versions_update = gr.update(choices=versions, value=(versions[0] if versions else None))
                return (
                    content, activity, content, False, banner, 
                    versions_update, 
                    gr.update(interactive=True), 
                    gr.update(visible=True), 
                    gr.update(visible=True), 
                    gr.update(visible=True), 
                    gr.update(visible=True), 
                    gr.update(visible=False)
                )

        file_select.change(_on_select, inputs=[file_select], outputs=[editor, activity_html, original_content, is_dirty, context_banner, versions_dd, editor, save_btn, revert_btn, save_version_btn, ai_assist_accordion, restore_as_canon_btn])
        
        def _on_editor_change(new_content, original, relpath):
            if not relpath or relpath.startswith('.versions/'):
                return gr.update(visible=True), False, gr.update(visible=False), gr.update(visible=False)
            
            dirty = (new_content != original)
            state_color = "#ff8c00" if dirty else "green"
            state_text = "⚠️ Modified (unsaved)" if dirty else "✅ Clean"
            banner = f"<div style='background:#f0f0f0;border-left:4px solid #666;padding:10px 14px;font-family:system-ui;'><strong>📌 Context:</strong> World Editor<br><strong>Path:</strong> {relpath}<br><strong>State:</strong> <span style='color:{state_color};'>{state_text}</span></div>"
            return banner, dirty, gr.update(visible=True), gr.update(visible=dirty)

        editor.change(_on_editor_change, inputs=[editor, original_content, file_select], outputs=[context_banner, is_dirty, save_btn, revert_btn])

        def _on_save(relpath, content):
            toast, out_content, tree_text, activity = save_file(relpath, content)
            toast_html_out = toast if (isinstance(toast, str) and toast.strip().startswith('<script>')) else show_toast(str(toast or 'Saved'), 'info')
            banner = f"<div style='background:#f0fdf4;border-left:4px solid #22c55e;padding:10px 14px;font-family:system-ui;'><strong>📌 Context:</strong> Canonical File<br><strong>Path:</strong> {relpath}<br><strong>State:</strong> <span style='color:green;'>✅ Clean (saved)</span></div>"
            versions = wb.list_versions(relpath) if relpath else []
            versions_update = gr.update(choices=versions, value=(versions[0] if versions else None))
            return toast_html_out, out_content, tree_text, activity, out_content, False, banner, versions_update, gr.update(visible=False)

        save_btn.click(_on_save, inputs=[file_select, editor], outputs=[toast_html, editor, world_tree, activity_html, original_content, is_dirty, context_banner, versions_dd, revert_btn])
        
        def _on_revert(original, relpath):
            banner = f"<div style='background:#f0fdf4;border-left:4px solid #22c55e;padding:10px 14px;font-family:system-ui;'><strong>📌 Context:</strong> Canonical File<br><strong>Path:</strong> {relpath}<br><strong>State:</strong> <span style='color:green;'>✅ Clean (reverted)</span></div>"
            return original, banner, False, gr.update(visible=False)

        def _on_load_version(relpath, version_id):
            if not version_id:
                return '', f"<div style='background:#f0f0f0;border-left:4px solid #666;padding:10px 14px;font-family:system-ui;'><strong>📌 Context:</strong> World Editor<br><strong>Path:</strong> {relpath}<br><strong>State:</strong> <span style='color:red;'>❌ No version selected</span></div>", False, '', gr.update(visible=False)
            content = wb.load_version(relpath, version_id)
            banner = f"<div style='background:#f0fdf4;border-left:4px solid #22c55e;padding:10px 14px;font-family:system-ui;'><strong>📌 Context:</strong> Canonical File<br><strong>Path:</strong> {relpath}<br><strong>State:</strong> <span style='color:green;'>✅ Loaded version: {version_id}</span></div>"
            return content or '', banner, False, content or '', gr.update(visible=False)


        def _on_restore_draft(relpath):
            draft = wb.restore_draft(relpath)
            if not draft:
                return '', f"<div style='background:#f0f0f0;border-left:4px solid #666;padding:10px 14px;font-family:system-ui;'><strong>📌 Context:</strong> World Editor<br><strong>Path:</strong> {relpath}<br><strong>State:</strong> <span style='color:red;'>❌ No draft found</span></div>", False, gr.update(visible=False)
            banner = f"<div style='background:#f0f0f0;border-left:4px solid #666;padding:10px 14px;font-family:system-ui;'><strong>📌 Context:</strong> World Editor<br><strong>Path:</strong> {relpath}<br><strong>State:</strong> <span style='color:#ff8c00;'>⚠️ Draft restored (unsaved)</span></div>"
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

import json
import os
from pathlib import Path
from . import indexer

try:
    import gradio as gr
except Exception:
    gr = None

INDEX_PATH = 'narrative_scripts_index.json'

def load_index(path=INDEX_PATH):
    if not os.path.isfile(path):
        return {"scripts": []}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {"scripts": []}

def build_ui():
    if gr is None:
        raise RuntimeError('gradio is not installed')

    def get_index():
        return load_index()

    index = get_index()
    categories = sorted({s['category'] for s in index.get('scripts', [])})

    with gr.Blocks() as demo:
        gr.Markdown("# Narrative Script Browser")
        
        with gr.Row():
            with gr.Column(scale=1):
                cat_dd = gr.Dropdown(choices=categories, label="Category")
                script_dd = gr.Dropdown(choices=[], label="Script")
                version_dd = gr.Dropdown(choices=[], label="Version")
                
            with gr.Column(scale=2):
                content_view = gr.Code(label="Content", language="markdown", interactive=False)
                notes_view = gr.Textbox(label="Version Notes", interactive=False)

        def _on_cat_change(cat):
            scripts = sorted({s['id'].split('/')[-1] for s in index['scripts'] if s['category'] == cat})
            return gr.update(choices=scripts, value=None), gr.update(choices=[], value=None), "", ""

        def _on_script_change(cat, script_name):
            if not cat or not script_name:
                return gr.update(choices=[], value=None), "", ""
            script_id = f"{cat}/{script_name}"
            item = next((s for s in index['scripts'] if s['id'] == script_id), None)
            if not item:
                return gr.update(choices=[], value=None), "", ""
            versions = item.get('versions', [])
            return gr.update(choices=versions, value=None), "", ""

        def _on_version_change(cat, script_name, version):
            if not cat or not script_name or not version:
                return "", ""
            # Logic to load version content and meta
            # This depends on the storage layout (scripts/versions/category/script/vN.txt)
            v_path = os.path.join('scripts', 'versions', cat, script_name, f"{version}.txt")
            m_path = os.path.join('scripts', 'versions', cat, script_name, "meta.json")
            
            content = ""
            if os.path.exists(v_path):
                with open(v_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            notes = ""
            if os.path.exists(m_path):
                with open(m_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                    v_meta = next((v for v in meta.get('versions', []) if v['version'] == version), None)
                    if v_meta:
                        notes = v_meta.get('notes', '')
            
            return content, notes

        cat_dd.change(_on_cat_change, inputs=[cat_dd], outputs=[script_dd, version_dd, content_view, notes_view])
        script_dd.change(_on_script_change, inputs=[cat_dd, script_dd], outputs=[version_dd, content_view, notes_view])
        version_dd.change(_on_version_change, inputs=[cat_dd, script_dd, version_dd], outputs=[content_view, notes_view])

    return demo

if __name__ == "__main__":
    demo = build_ui()
    demo.launch()

import os
import json
import importlib.util

spec = importlib.util.spec_from_file_location('world_builder', os.path.join(os.getcwd(), 'scripts', 'world_builder.py'))
wb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wb)

import src.ui as ui


def test_handle_confirm_save_creates_version_and_meta(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # create a canonical file to version
    os.makedirs('world_db', exist_ok=True)
    with open(os.path.join('world_db', 'foo.md'), 'w', encoding='utf-8') as f:
        f.write('orig')
    payload = json.dumps({'action': 'save_new_version', 'rel': 'foo.md', 'content': 'new content', 'notes': 'note1'})
    toast, versions_update, confirm_modal, confirm_yes, confirm_no, pending = ui.handle_confirm_save(payload)
    assert isinstance(toast, str)
    # verify versions dir created
    vd = wb._versions_dir_for('foo.md')
    assert os.path.isdir(vd)
    files = [f for f in os.listdir(vd) if f.endswith('.md')]
    assert files, 'No .md in versions dir'
    # meta exists
    meta = files[0] + '.meta.json'
    assert os.path.exists(os.path.join(vd, meta))


def test_handle_confirm_cancel():
    res = ui.handle_confirm_cancel('{}')
    assert isinstance(res[0], str) and 'Cancelled' in res[0]
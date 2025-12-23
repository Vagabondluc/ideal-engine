import os
import json
import importlib.util

import src.world_builder as wb
import src.ui as ui


def test_handle_action_unrecognized():
    res = ui.handle_action_json('')
    assert 'Unrecognized action' in res


def test_handle_action_retry_calls_perform_retry(monkeypatch):
    # patch the module instance that `src.ui` references so the handler uses our stub
    monkeypatch.setattr(ui.wb, 'perform_retry', lambda rid: "<script>showWBToast('✅ Retry succeeded','info');</script>")
    payload = json.dumps({'action': 'retry', 'retry_id': 'rid1'})
    res = ui.handle_action_json(payload)
    assert 'Retry succeeded' in res


def test_handle_action_open_folder_success(monkeypatch, tmp_path):
    # set cwd to tmp workspace
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'world_db' / 'subdir').mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(wb, 'open_folder', lambda path: (True, f'Opened {path}'))
    payload = json.dumps({'action': 'open_folder', 'path': str(tmp_path / 'world_db' / 'subdir')})
    res = ui.handle_action_json(payload)
    assert 'Opened' in res


def test_save_new_version_writes_meta(tmp_path, monkeypatch):
    # Use a temporary working directory so we don't touch repo files
    monkeypatch.chdir(tmp_path)
    os.makedirs('world_db', exist_ok=True)
    with open(os.path.join('world_db', 'foo.txt'), 'w', encoding='utf-8') as f:
        f.write('original')
    res = wb.save_new_version('foo.txt', 'newcontent', notes='my note')
    assert 'Saved version' in res or '✅ Saved version' in res
    vd = wb._versions_dir_for('foo.txt')
    assert os.path.isdir(vd)
    files = [f for f in os.listdir(vd) if f.endswith('.md')]
    assert files, 'No version .md files found'
    # ensure meta exists
    first = files[0]
    meta_path = os.path.join(vd, first + '.meta.json')
    assert os.path.exists(meta_path)
    with open(meta_path, 'r', encoding='utf-8') as mf:
        meta = json.load(mf)
    assert meta.get('notes') == 'my note'
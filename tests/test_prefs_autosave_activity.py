from pathlib import Path
import importlib


def test_config_persistence(tmp_path, monkeypatch):
    # Load module fresh
    mb = importlib.reload(__import__('scripts.world_builder', fromlist=['*']))
    wb = mb
    cfg_path = tmp_path / 'wb_config.json'
    wb.CONFIG_PATH = cfg_path

    wb.SHOW_ADVANCED_ERRORS = True
    wb.AUTOSAVE_ENABLED = False
    wb.save_config()

    # flip values then reload
    wb.SHOW_ADVANCED_ERRORS = False
    wb.AUTOSAVE_ENABLED = True
    wb.load_config()

    assert wb.SHOW_ADVANCED_ERRORS is True
    assert wb.AUTOSAVE_ENABLED is False


def test_autosave_and_draft_persistence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mb = importlib.reload(__import__('scripts.world_builder', fromlist=['*']))
    wb = mb

    # Ensure no drafts initially
    assert wb.find_draft('foo.md') is None

    wb.AUTOSAVE_ENABLED = False
    ok = wb.persist_draft('foo.md', 'hello world')
    assert ok is False
    assert wb.find_draft('foo.md') is None

    # Force save should bypass autosave flag
    ok = wb.persist_draft('foo.md', 'hello world', force=True)
    assert ok is True
    assert wb.find_draft('foo.md') == 'hello world'

    # Clear draft
    assert wb.clear_draft('foo.md') is True
    assert wb.find_draft('foo.md') is None


def test_activity_log_and_clear(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mb = importlib.reload(__import__('scripts.world_builder', fromlist=['*']))
    wb = mb

    # Ensure world_db dir is used under tmp_path via chdir
    wb.log_activity('Test entry 1')
    p = Path('world_db') / '.activity.log'
    assert p.exists()

    html = wb.get_activity_log_html()
    assert 'Test entry 1' in html

    # Clear activity log (should create backup)
    _ = wb.clear_activity()
    bak = Path('world_db') / '.activity.log.bak'
    assert bak.exists()
    # After clear, log should show no activity
    html2 = wb.get_activity_log_html()
    assert 'No activity yet' in html2 or 'No activity' in html2

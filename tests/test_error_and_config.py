from pathlib import Path

from scripts import world_builder as wb

CONFIG_PATH = Path('.world_builder_config.json')
DRAFTS_DIR = Path('world_db') / '.drafts'
ACT_LOG = Path('world_db') / '.activity.log'


def teardown_function(fn):
    # cleanup config and drafts after each test
    try:
        if CONFIG_PATH.exists():
            CONFIG_PATH.unlink()
    except Exception:
        pass
    try:
        if DRAFTS_DIR.exists():
            for f in DRAFTS_DIR.rglob('*.draft.md'):
                f.unlink()
    except Exception:
        pass
    try:
        if ACT_LOG.exists():
            ACT_LOG.unlink()
    except Exception:
        pass


def test_config_persistence_roundtrip(tmp_path, monkeypatch):
    # Ensure starting defaults
    if CONFIG_PATH.exists():
        CONFIG_PATH.unlink()
    wb.SHOW_ADVANCED_ERRORS = False
    wb.AUTOSAVE_ENABLED = True

    # Change and save
    wb.SHOW_ADVANCED_ERRORS = True
    wb.AUTOSAVE_ENABLED = False
    wb.save_config()

    # Reset in-memory and reload
    wb.SHOW_ADVANCED_ERRORS = False
    wb.AUTOSAVE_ENABLED = True
    wb.load_config()

    assert wb.SHOW_ADVANCED_ERRORS is True
    assert wb.AUTOSAVE_ENABLED is False


def test_autosave_respected(tmp_path, monkeypatch):
    # Ensure autosave off prevents drafts unless forced
    wb.AUTOSAVE_ENABLED = False
    rel = 'test.md'
    content = 'hello world'
    dp = Path(wb.draft_path_for(rel))
    if dp.exists():
        dp.unlink()
    # should not create draft without force
    assert wb.persist_draft(rel, content, force=False) is False
    assert not dp.exists()
    # now force
    assert wb.persist_draft(rel, content, force=True) is True
    assert dp.exists()
    assert dp.read_text(encoding='utf-8') == content


def test_activity_log_write_and_read(tmp_path):
    # Append some entries and read via helper
    Path('world_db').mkdir(exist_ok=True)
    if ACT_LOG.exists():
        ACT_LOG.unlink()
    wb.log_activity('unit-test entry one')
    wb.log_activity('unit-test entry two')
    html = wb.get_activity_log_html()
    assert 'unit-test entry one' in html
    assert 'unit-test entry two' in html


def test_format_error_enhanced_includes_actions():
    html = wb.format_error_enhanced('T', detail='d', suggestions=['s1'], stderr='err', show_advanced=True, retry_id='rid123', folder_path='C:/tmp')
    assert 'Copy details' in html
    assert 'Retry' in html
    assert 'Open containing folder' in html
    assert 'Show full details' in html

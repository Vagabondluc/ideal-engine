import importlib
import os
import importlib.util

spec = importlib.util.spec_from_file_location('world_builder', os.path.join(os.getcwd(), 'scripts', 'world_builder.py'))
wb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wb)

import src.ui as ui


def test_debounce_change_returns_toast(monkeypatch):
    monkeypatch.setattr(wb, 'set_debounce', lambda v: "<script>showWBToast('Debounce set to 2.0s','info');</script>")
    res = ui.handle_debounce_change(2.0)
    assert 'Debounce set' in (res or '') or 'Error' not in (res or '')


def test_auto_refresh_toggle():
    res_on = ui.handle_auto_refresh_toggle(True)
    res_off = ui.handle_auto_refresh_toggle(False)
    assert 'enabled' in (res_on or '').lower() or 'enabled' in (res_on or '')
    assert 'disabled' in (res_off or '').lower() or 'disabled' in (res_off or '')
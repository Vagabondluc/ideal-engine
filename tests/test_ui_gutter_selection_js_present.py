from src.ui import APP_STYLE


def test_gutter_selection_js_present():
    assert 'updateActiveGutter' in APP_STYLE
    assert 'selectLineInEditor' in APP_STYLE
    assert 'getOffsetWithin' in APP_STYLE
    assert 'wb-gutter-line active' not in APP_STYLE  # class is added dynamically

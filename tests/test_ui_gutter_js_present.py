from src.ui import APP_STYLE


def test_gutter_js_injected():
    # Ensure APP_STYLE contains gutter hooks
    assert 'wb-gutter-lines' in APP_STYLE
    assert 'gutterClickHandler' in APP_STYLE
    assert 'wb-gutter-line' in APP_STYLE

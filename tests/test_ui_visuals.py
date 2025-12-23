from src.ui import APP_STYLE


def test_visuals_css_present():
    assert "wb-gutter-line.active" in APP_STYLE
    assert "JetBrains Mono" in APP_STYLE or "ui-monospace" in APP_STYLE
    assert "box-shadow:inset 3px 0 0" in APP_STYLE

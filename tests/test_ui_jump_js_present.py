from src.ui import APP_STYLE


def test_jump_to_line_present():
    assert 'showJumpToLinePrompt' in APP_STYLE
    assert 'submitJump' in APP_STYLE
    assert 'wb-jump-modal' in APP_STYLE

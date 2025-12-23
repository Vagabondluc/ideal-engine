from src.ui import show_toast


def test_show_toast_returns_script():
    s = show_toast('Hello world', 'info')
    assert "showWBToast" in s
    assert 'Hello world' in s


def test_show_toast_encodes_json():
    s = show_toast("He said: \"Hi\"", 'info')
    # should be a script that calls showWBToast with a JSON string
    assert s.strip().startswith('<script>') and s.strip().endswith("</script>")

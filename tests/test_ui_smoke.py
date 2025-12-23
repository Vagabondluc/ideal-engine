import src.ui as ui


def test_create_app_and_run_model_smoke():
    app = ui.create_app()
    assert app is not None
    # quick smoke: run_model should accept inputs and return a tuple
    out, toast = ui.run_model('hello world', 'mistral:latest', 0.7)
    assert isinstance(out, str)
    assert isinstance(toast, str)
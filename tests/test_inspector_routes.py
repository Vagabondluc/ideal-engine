from src.handlers import test_inspector as ti


class DummyApp:
    def __init__(self):
        self.routes = []
    def add_api_route(self, path, handler, methods=None):
        self.routes.append((path, methods))


def test_register_routes_on_dummy_app():
    app = DummyApp()
    ok = ti.register_test_inspector_routes(app)
    assert ok is True
    assert any(p == '/__wb_test/inspector_signals' for p, _ in app.routes)

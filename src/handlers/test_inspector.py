import os
import json
from typing import Dict, Any

WB_HANDSHAKE_ENV = 'WB_E2E_HANDSHAKE'


def inspector_signals_response(headers: Dict[str, str], query: Dict[str, str]) -> Dict[str, Any]:
    """Return a dict with keys: status, body, content_type.

    headers: dict-like of incoming request headers (case-insensitive expected)
    query: dict-like of query params

    This function is pure and testable without an HTTP server.
    """
    token = os.environ.get(WB_HANDSHAKE_ENV)
    # If handshake not enabled, return 404-like
    if not token:
        return {'status': 404, 'body': json.dumps({'error': 'handshake not enabled'}), 'content_type': 'application/json'}

    handshake_header = None
    # headers may have different casing
    for k, v in headers.items():
        if k.lower() == 'x-wb-e2e-handshake':
            handshake_header = v
            break
    if handshake_header != token:
        return {'status': 401, 'body': json.dumps({'error': 'invalid handshake header'}), 'content_type': 'application/json'}

    # Build deterministic signals based on query params
    trace_id = query.get('traceId', 'trace-01')
    # Basic inspector-ready signal
    signals = [{'type': 'inspector-ready', 'payload': {'nodeId': 'root', 'traceId': trace_id, 'timestamp': '2025-01-01T00:00:00Z'}}]
    inspector_html = '<div id="inspector">deterministic</div>'
    if query.get('signals'):
        # allow specifying 'open-intent' etc. as comma-separated list
        requested = [s.strip() for s in query.get('signals','').split(',') if s.strip()]
        signals = []
        for s in requested:
            if s == 'inspector-ready':
                signals.append({'type': 'inspector-ready', 'payload': {'nodeId': 'root', 'traceId': trace_id, 'timestamp': '2025-01-01T00:00:00Z'}})
            else:
                signals.append({'type': s, 'payload': {'nodeId': 'root', 'traceId': trace_id, 'timestamp': '2025-01-01T00:00:00Z'}})
    if query.get('html', '').lower() in ('1', 'true', 'yes'):
        return {'status': 200, 'body': inspector_html, 'content_type': 'text/html'}

    body = {'signals': signals, 'inspectorHtml': inspector_html}
    return {'status': 200, 'body': json.dumps(body), 'content_type': 'application/json'}


# Utility to register routes on a Starlette/FastAPI app or Gradio app wrapper
def register_test_inspector_routes(app):
    """Attempt to register a route '/__wb_test/inspector_signals' on the given Gradio Blocks 'app'.

    This function tolerantly tries to attach to common underlying app objects.
    """
    try:
        # Try common accessors used by Gradio
        starlette_app = None
        if hasattr(app, 'add_api_route') or hasattr(app, 'add_route'):
            starlette_app = app
        elif hasattr(app, 'app'):
            starlette_app = app.app
        elif hasattr(app, 'server'):
            starlette_app = app.server
        elif hasattr(app, 'server_app'):
            starlette_app = app.server_app
        else:
            starlette_app = getattr(app, 'app', None)
        if starlette_app is None:
            return False

        from starlette.responses import JSONResponse, PlainTextResponse
        from starlette.requests import Request

        async def _handler(request: Request):
            headers = {k: v for k, v in request.headers.items()}
            query = {k: v for k, v in request.query_params.items()}
            resp = inspector_signals_response(headers, query)
            if resp['content_type'].startswith('application/json'):
                return JSONResponse(status_code=resp['status'], content=json.loads(resp['body']))
            else:
                return PlainTextResponse(content=resp['body'], status_code=resp['status'], media_type=resp['content_type'])

        # starlette_app could be FastAPI or Starlette; use add_api_route if available
        if hasattr(starlette_app, 'add_api_route'):
            starlette_app.add_api_route('/__wb_test/inspector_signals', _handler, methods=['GET'])
        elif hasattr(starlette_app, 'add_route'):
            starlette_app.add_route('/__wb_test/inspector_signals', _handler, methods=['GET'])
        else:
            return False
        return True
    except Exception:
        return False

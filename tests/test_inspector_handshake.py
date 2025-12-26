import os
import json
import pytest
from src.handlers import test_inspector as ti


def test_requiresHandshakeHeader(monkeypatch):
    # Ensure env unset -> 404
    monkeypatch.delenv(ti.WB_HANDSHAKE_ENV, raising=False)
    resp = ti.inspector_signals_response({}, {})
    assert resp['status'] == 404

    # Set env but missing header -> 401
    monkeypatch.setenv(ti.WB_HANDSHAKE_ENV, 'token123')
    resp = ti.inspector_signals_response({}, {})
    assert resp['status'] == 401

    # Wrong header -> 401
    resp = ti.inspector_signals_response({'X-WB-E2E-HANDSHAKE': 'wrong'}, {})
    assert resp['status'] == 401


def test_returnsDeterministicSignalsWithHandshake(monkeypatch):
    monkeypatch.setenv(ti.WB_HANDSHAKE_ENV, 'token123')
    headers = {'X-WB-E2E-HANDSHAKE': 'token123'}
    resp = ti.inspector_signals_response(headers, {})
    assert resp['status'] == 200
    body = json.loads(resp['body'])
    assert 'signals' in body and isinstance(body['signals'], list)
    assert body['signals'][0]['type'] == 'inspector-ready'
    assert 'inspectorHtml' in body and '<div id="inspector">' in body['inspectorHtml']


def test_html_query_param_returns_html(monkeypatch):
    monkeypatch.setenv(ti.WB_HANDSHAKE_ENV, 'token123')
    headers = {'X-WB-E2E-HANDSHAKE': 'token123'}
    resp = ti.inspector_signals_response(headers, {'html':'true'})
    assert resp['status'] == 200
    assert resp['content_type'] == 'text/html'
    assert '<div id="inspector">' in resp['body']

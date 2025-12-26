import json
import re
import pytest
from unittest import mock

import src.ui as ui
import src.world_builder as wb


def extract_dynamic_payload(toast_html: str):
    m = re.search(r"handleDynamicSaveResponse\((\{[\s\S]*?\})\)", toast_html)
    if not m:
        return None
    return json.loads(m.group(1))


def test_returnsValidationErrorsWithoutThrowing(tmp_path, monkeypatch):
    # Arrange: patch get_card_form_fields to return a required 'name' field
    def _get_fields(uuid, base_dir=None):
        return [{'key': 'name', 'type': 'text', 'required': True}]
    monkeypatch.setattr(wb, 'get_card_form_fields', _get_fields)

    # Act: call handler with missing name
    payload = {'action': 'save_card_form_dynamic', 'uuid': 'test-uuid', 'formData': {'name': ''}}
    res = ui.handle_action_json(json.dumps(payload))

    # Assert: returned toast contains handleDynamicSaveResponse with expected shape
    assert isinstance(res, tuple)
    toast = res[0]
    dyn = extract_dynamic_payload(toast)
    assert dyn is not None, 'Dynamic payload not found in toast HTML'
    assert dyn.get('ok') is False
    assert 'rowErrors' in dyn and 'name' in dyn['rowErrors']
    err_items = dyn['rowErrors']['name']
    assert isinstance(err_items, list) and len(err_items) >= 1
    e = err_items[0]
    assert e['path'] == 'fields.name'
    assert 'required' in e['message'].lower()
    assert 'firstInvalidKey' in dyn and dyn['firstInvalidKey'] == 'name'


def test_doesNotCallPersistenceOnValidationError(tmp_path, monkeypatch):
    # Arrange
    def _get_fields(uuid, base_dir=None):
        return [{'key': 'name', 'type': 'text', 'required': True}]
    monkeypatch.setattr(wb, 'get_card_form_fields', _get_fields)
    spy = mock.Mock(return_value=True)
    monkeypatch.setattr(wb, 'save_card_form_fields', spy)

    payload = {'action': 'save_card_form_dynamic', 'uuid': 'test-uuid', 'formData': {'name': ''}}
    res = ui.handle_action_json(json.dumps(payload))

    # Assert: persistence not called
    assert not spy.called


def test_selectsDeterministicFirstInvalidKey(tmp_path, monkeypatch):
    # two fields, both required; expect firstInvalidKey == first field's key
    def _get_fields(uuid, base_dir=None):
        return [{'key': 'a', 'type': 'text', 'required': True}, {'key': 'b', 'type': 'text', 'required': True}]
    monkeypatch.setattr(wb, 'get_card_form_fields', _get_fields)

    payload = {'action': 'save_card_form_dynamic', 'uuid': 'test-uuid', 'formData': {'a': '', 'b': ''}}
    res = ui.handle_action_json(json.dumps(payload))
    toast = res[0]
    dyn = extract_dynamic_payload(toast)
    assert dyn is not None
    assert dyn['firstInvalidKey'] == 'a'


def test_returns500OnUnexpectedInternalError(tmp_path, monkeypatch):
    # Simulate persistence raising an unexpected error on save path
    def _get_fields(uuid, base_dir=None):
        return [{'key': 'name', 'type': 'text', 'required': False}]
    monkeypatch.setattr(wb, 'get_card_form_fields', _get_fields)

    def bad_save(uuid, formData, base_dir=None):
        raise RuntimeError('boom')
    monkeypatch.setattr(wb, 'save_card_form_fields', bad_save)

    payload = {'action': 'save_card_form_dynamic', 'uuid': 'test-uuid', 'formData': {'name': 'ok'}}
    res = ui.handle_action_json(json.dumps(payload))

    # The handler should not crash; it should return an error toast string
    assert isinstance(res, tuple)
    toast = res[0]
    assert 'Error saving' in toast or 'Inspector save error' in toast

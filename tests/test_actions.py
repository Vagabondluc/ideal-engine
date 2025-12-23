import os
import importlib.util

import src.world_builder as wb


def test_perform_retry_unknown():
    res = wb.perform_retry('no-such-id')
    assert 'Unknown retry id' in res or 'Retry not available' in res


def test_open_folder_nonexistent(tmp_path):
    ok, msg = wb.open_folder(str(tmp_path / 'does_not_exist'))
    assert ok is False
    assert 'does not exist' in msg or 'Not allowed' in msg or 'Error' in msg

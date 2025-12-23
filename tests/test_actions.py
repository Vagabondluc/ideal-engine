import os
import importlib.util

# import scripts.world_builder by path
spec = importlib.util.spec_from_file_location('world_builder', os.path.join(os.getcwd(), 'scripts', 'world_builder.py'))
wb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wb)


def test_perform_retry_unknown():
    res = wb.perform_retry('no-such-id')
    assert 'Unknown retry id' in res or 'Retry not available' in res


def test_open_folder_nonexistent(tmp_path):
    ok, msg = wb.open_folder(str(tmp_path / 'does_not_exist'))
    assert ok is False
    assert 'does not exist' in msg or 'Not allowed' in msg or 'Error' in msg

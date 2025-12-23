import os
import shutil
import uuid
import importlib.util

# import the module under test by file path
spec = importlib.util.spec_from_file_location('world_builder', os.path.join(os.getcwd(), 'scripts', 'world_builder.py'))
wb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wb)


def make_temp_rel():
    name = f'test_tmp_{uuid.uuid4().hex[:8]}'
    return os.path.join(name, 'sample.md')


def test_save_editor_and_revert():
    rel = make_temp_rel()
    content = '# Hello\nThis is a test.'

    # Ensure there's no existing file
    path = os.path.join('world_db', rel)
    if os.path.exists(path):
        os.remove(path)

    # Save
    res = wb.save_editor(rel, content)
    # save_editor now returns multiple fields: (status, content, tree_upd, files_upd, ctx_html, warn)
    if isinstance(res, tuple):
        status = res[0]
        _ = res[1]
    else:
        status = res
        _ = ''
    assert '✅ Saved' in status
    assert os.path.exists(path)

    # Revert should return the same content
    rev_res = wb.revert_editor(rel)
    if isinstance(rev_res, tuple):
        rev_status = rev_res[0]
        rev_content = rev_res[1]
    else:
        rev_status, rev_content = rev_res
    assert 'Reverted' in rev_status
    assert content == rev_content

    # Cleanup
    try:
        shutil.rmtree(os.path.dirname(path))
    except Exception:
        pass


def test_save_new_version_creates_version_file():
    rel = make_temp_rel()
    content = '# Version test\nVersion content'

    # Ensure canonical exists
    dest = os.path.join('world_db', rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, 'w', encoding='utf-8') as f:
        f.write('# original')

    # Save new version
    status = wb.save_new_version(rel, content)
    # save_new_version may return a tuple (message, tree_upd, files_upd)
    if isinstance(status, tuple):
        status_msg = status[0]
    else:
        status_msg = status
    assert isinstance(status_msg, str) and status_msg.startswith('✅'), f"Unexpected status: {status}"

    # Versions dir should contain a file
    safe_rel = rel.replace('..', '').lstrip('/')
    vers_dir = os.path.join('world_db', '.versions', os.path.dirname(safe_rel), os.path.basename(safe_rel))
    files = []
    if os.path.exists(vers_dir):
        files = os.listdir(vers_dir)
    assert files, 'No version files created'

    # Cleanup
    try:
        shutil.rmtree(os.path.dirname(dest))
        shutil.rmtree(os.path.join('world_db', '.versions', os.path.dirname(safe_rel)))
    except Exception:
        pass

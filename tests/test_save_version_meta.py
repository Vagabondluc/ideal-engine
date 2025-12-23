import importlib.util, os
spec = importlib.util.spec_from_file_location('world_builder', os.path.join(os.getcwd(), 'scripts', 'world_builder.py'))
wb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wb)


def test_save_new_version_writes_meta():
    rel = 'test_tmp_meta/mfile.md'
    content = '# test\nmeta'
    dest = os.path.join('world_db', rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, 'w', encoding='utf-8') as f:
        f.write('# original')
    res = wb.save_new_version(rel, content, notes='Important note')
    assert isinstance(res, str) and res.startswith('✅')
    # find created version file and meta file
    vd = os.path.join('world_db', '.versions', os.path.dirname(rel), os.path.basename(rel))
    files = os.listdir(vd)
    md_files = [f for f in files if f.endswith('.md')]
    meta_files = [f for f in files if f.endswith('.meta.json')]
    assert md_files and meta_files, 'Expected both md and meta files'
    # cleanup
    try:
        import shutil
        shutil.rmtree(os.path.dirname(dest))
        shutil.rmtree(os.path.join('world_db', '.versions', os.path.dirname(rel)))
    except Exception:
        pass

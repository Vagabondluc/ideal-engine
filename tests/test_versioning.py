import os
import tempfile
import shutil
import unittest

from scripts import indexer


class TestVersioning(unittest.TestCase):
    def test_add_version_creates_file_and_updates_index(self):
        tmp = tempfile.mkdtemp()
        scripts_root = os.path.join(tmp, 'scripts')
        canonical = os.path.join(scripts_root, 'canonical', 'AI_Behavior')
        os.makedirs(canonical, exist_ok=True)

        canon_path = os.path.join(canonical, 'ed_greenwood.txt')
        with open(canon_path, 'w', encoding='utf-8') as f:
            f.write('canonical content')

        out = indexer.add_version(scripts_root, 'AI_Behavior', 'ed_greenwood', 'my version content', 'note')
        self.assertTrue(os.path.exists(out))
        # index.json should be created and include the new version
        idx_path = os.path.join(scripts_root, 'index.json')
        self.assertTrue(os.path.exists(idx_path))
        with open(idx_path, 'r', encoding='utf-8') as f:
            idx = f.read()
        self.assertIn('ed_greenwood', idx)

        shutil.rmtree(tmp)


if __name__ == '__main__':
    unittest.main()

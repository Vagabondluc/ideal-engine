import os
import tempfile
import shutil
import unittest

from scripts import indexer


class TestUILoadVersion(unittest.TestCase):
    def test_load_version_path_and_content(self):
        tmp = tempfile.mkdtemp()
        scripts_root = os.path.join(tmp, 'scripts')
        canonical = os.path.join(scripts_root, 'canonical', 'AI_Behavior')
        os.makedirs(canonical, exist_ok=True)

        canon_path = os.path.join(canonical, 'ed_greenwood.txt')
        with open(canon_path, 'w', encoding='utf-8') as f:
            f.write('canonical content')

        _ = indexer.add_version(scripts_root, 'AI_Behavior', 'ed_greenwood', 'version content', 'note')
        # compute expected version path
        version_dir = os.path.join(scripts_root, 'versions', 'AI_Behavior', 'ed_greenwood')
        files = [f for f in os.listdir(version_dir) if f.endswith('.txt')]
        self.assertTrue(len(files) >= 1)
        vfile = os.path.join(version_dir, files[-1])
        with open(vfile, 'r', encoding='utf-8') as f:
            txt = f.read()
        self.assertEqual(txt, 'version content')

        shutil.rmtree(tmp)


if __name__ == '__main__':
    unittest.main()

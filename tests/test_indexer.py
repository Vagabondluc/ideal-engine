import os
import tempfile
import shutil
import unittest

from scripts import indexer


class TestIndexer(unittest.TestCase):
    def test_generate_index_basic(self):
        tmp = tempfile.mkdtemp()
        scripts_root = os.path.join(tmp, 'scripts')
        canonical = os.path.join(scripts_root, 'canonical', 'AI_Behavior')
        versions = os.path.join(scripts_root, 'versions', 'AI_Behavior', 'ed_greenwood')
        os.makedirs(canonical, exist_ok=True)
        os.makedirs(versions, exist_ok=True)

        # create a canonical script
        canon_path = os.path.join(canonical, 'ed_greenwood.txt')
        with open(canon_path, 'w', encoding='utf-8') as f:
            f.write('canonical content')

        # add a version
        with open(os.path.join(versions, 'v1.txt'), 'w', encoding='utf-8') as f:
            f.write('v1')

        idx = indexer.generate_index(scripts_root)
        self.assertIn('scripts', idx)
        scripts = idx['scripts']
        self.assertGreaterEqual(len(scripts), 1)
        found = [s for s in scripts if s['id'] == 'AI_Behavior/ed_greenwood']
        self.assertEqual(len(found), 1)
        self.assertIn('v1', found[0]['versions'])

        shutil.rmtree(tmp)


if __name__ == '__main__':
    unittest.main()

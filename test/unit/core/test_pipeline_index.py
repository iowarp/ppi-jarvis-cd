"""
Tests for pipeline_index.py - Pipeline Index Manager
"""
import unittest
import sys
import os
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from jarvis_cd.core.pipeline_index import PipelineIndexManager
from jarvis_cd.core.config import Jarvis


class TestPipelineIndexManager(unittest.TestCase):
    """Tests for PipelineIndexManager class"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp(prefix='jarvis_test_ppl_index_')
        self.jarvis_root = os.path.join(self.test_dir, '.ppi-jarvis')
        self.config_dir = os.path.join(self.test_dir, 'config')
        self.private_dir = os.path.join(self.test_dir, 'private')
        self.shared_dir = os.path.join(self.test_dir, 'shared')

        os.makedirs(self.jarvis_root, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.private_dir, exist_ok=True)
        os.makedirs(self.shared_dir, exist_ok=True)

        # Reset and initialize Jarvis singleton
        Jarvis._instance = None
        self.config = Jarvis(self.jarvis_root)
        self.config.initialize(self.config_dir, self.private_dir, self.shared_dir)
        self.manager = PipelineIndexManager(self.config)

    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_parse_index_query_simple(self):
        """Test parsing simple index query"""
        repo, subdirs, script = self.manager.parse_index_query('myrepo.script')
        self.assertEqual(repo, 'myrepo')
        self.assertEqual(subdirs, [])
        self.assertEqual(script, 'script')

    def test_parse_index_query_with_subdirs(self):
        """Test parsing index query with subdirectories"""
        repo, subdirs, script = self.manager.parse_index_query('myrepo.sub1.sub2.script')
        self.assertEqual(repo, 'myrepo')
        self.assertEqual(subdirs, ['sub1', 'sub2'])
        self.assertEqual(script, 'script')

    def test_parse_index_query_invalid_no_dot(self):
        """Test invalid query without dot"""
        with self.assertRaises(ValueError) as context:
            self.manager.parse_index_query('nodotquery')
        self.assertIn('Invalid index query', str(context.exception))

    def test_parse_index_query_invalid_empty(self):
        """Test invalid empty query"""
        with self.assertRaises(ValueError):
            self.manager.parse_index_query('')

    def test_find_repo_path_builtin(self):
        """Test finding builtin repo path"""
        path = self.manager.find_repo_path('builtin')
        self.assertIsNotNone(path)
        self.assertTrue(isinstance(path, Path))

    def test_find_repo_path_nonexistent(self):
        """Test finding non-existent repo"""
        path = self.manager.find_repo_path('nonexistent_repo_xyz')
        self.assertIsNone(path)

    def test_find_pipeline_script_nonexistent_repo(self):
        """Test finding script in non-existent repo"""
        script = self.manager.find_pipeline_script('nonexistent.script')
        self.assertIsNone(script)

    def test_initialization(self):
        """Test PipelineIndexManager initialization"""
        self.assertIsNotNone(self.manager.jarvis_config)
        self.assertEqual(self.manager.jarvis_config, self.config)


if __name__ == '__main__':
    unittest.main()

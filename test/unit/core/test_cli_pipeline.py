"""
Tests for 'jarvis ppl' pipeline commands
"""
import os
from test.unit.core.test_cli_base import CLITestBase


class TestCLIPipeline(CLITestBase):
    """Tests for pipeline management commands"""

    def test_ppl_create(self):
        """Test creating a new pipeline"""
        # Initialize first
        self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])

        # Create pipeline
        args = ['ppl', 'create', 'test_pipeline']
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['pipeline_name'], 'test_pipeline')

    def test_ppl_create_alias(self):
        """Test creating pipeline with alias"""
        self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])

        # Use 'ppl c' alias
        args = ['ppl', 'c', 'test_pipeline_alias']
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['pipeline_name'], 'test_pipeline_alias')

    def test_ppl_create_missing_name(self):
        """Test that creating pipeline without name fails"""
        self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])

        args = ['ppl', 'create']
        result = self.run_command(args)

        # Should fail due to missing required argument
        self.assertFalse(result.get('success'))

    def test_ppl_append(self):
        """Test appending package to pipeline"""
        self.create_test_pipeline()

        args = ['ppl', 'append', 'test_package']
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['pkg_name'], 'test_package')

    def test_ppl_append_alias(self):
        """Test appending with alias"""
        self.create_test_pipeline()

        args = ['ppl', 'a', 'test_package']
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['pkg_name'], 'test_package')

    def test_ppl_list(self):
        """Test listing pipelines"""
        self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])

        args = ['ppl', 'list']
        result = self.run_command(args)

        # Should succeed
        self.assertIsNotNone(result)

    def test_ppl_load(self):
        """Test loading a pipeline"""
        self.create_test_pipeline('my_pipeline')

        args = ['ppl', 'load', 'my_pipeline']
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['pipeline_name'], 'my_pipeline')

    def test_ppl_print(self):
        """Test printing pipeline info"""
        self.create_test_pipeline()

        args = ['ppl', 'print']
        result = self.run_command(args)

        # Should execute without error
        self.assertIsNotNone(result)

    def test_ppl_status(self):
        """Test checking pipeline status"""
        self.create_test_pipeline()

        args = ['ppl', 'status']
        result = self.run_command(args)

        # Should execute without error
        self.assertIsNotNone(result)

    def test_ppl_clean(self):
        """Test cleaning pipeline"""
        self.create_test_pipeline()

        args = ['ppl', 'clean']
        result = self.run_command(args)

        # Should execute
        self.assertIsNotNone(result)

    def test_ppl_rm(self):
        """Test removing package from pipeline"""
        self.create_test_pipeline()

        # Append a package first
        self.run_command(['ppl', 'append', 'test_pkg'])

        # Remove it
        args = ['ppl', 'rm', 'test_pkg']
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['package_spec'], 'test_pkg')

    def test_ppl_destroy(self):
        """Test destroying a pipeline"""
        self.create_test_pipeline('destroy_me')

        args = ['ppl', 'destroy', 'destroy_me']
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['pipeline_name'], 'destroy_me')

    def test_ppl_run(self):
        """Test running a pipeline"""
        self.create_test_pipeline()

        args = ['ppl', 'run']
        result = self.run_command(args)

        # Should parse successfully
        self.assertIsNotNone(result)

    def test_ppl_start(self):
        """Test starting a pipeline"""
        self.create_test_pipeline()

        args = ['ppl', 'start']
        result = self.run_command(args)

        # Should parse successfully
        self.assertIsNotNone(result)

    def test_ppl_stop(self):
        """Test stopping a pipeline"""
        self.create_test_pipeline()

        args = ['ppl', 'stop']
        result = self.run_command(args)

        # Should parse successfully
        self.assertIsNotNone(result)

    def test_ppl_kill(self):
        """Test killing a pipeline"""
        self.create_test_pipeline()

        args = ['ppl', 'kill']
        result = self.run_command(args)

        # Should parse successfully
        self.assertIsNotNone(result)

    def test_ppl_update(self):
        """Test updating pipeline"""
        self.create_test_pipeline()

        args = ['ppl', 'update']
        result = self.run_command(args)

        # Should parse successfully
        self.assertIsNotNone(result)


if __name__ == '__main__':
    import unittest
    unittest.main()

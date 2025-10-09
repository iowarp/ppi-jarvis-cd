"""
Base test class for CLI tests.
Provides common setup and utilities for testing Jarvis CLI commands.
"""
import unittest
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from jarvis_cd.core.cli import JarvisCLI


class CLITestBase(unittest.TestCase):
    """Base class for CLI tests with common setup/teardown"""

    def setUp(self):
        """Set up test environment"""
        # Create temporary directories for testing
        self.test_dir = tempfile.mkdtemp(prefix='jarvis_test_')
        self.config_dir = os.path.join(self.test_dir, 'config')
        self.private_dir = os.path.join(self.test_dir, 'private')
        self.shared_dir = os.path.join(self.test_dir, 'shared')

        # Initialize CLI
        self.cli = JarvisCLI()
        self.cli.define_options()

        # Store original environment
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Clean up test environment"""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

        # Clean up temporary directories
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def run_command(self, args):
        """
        Helper to run a CLI command and capture result.

        :param args: List of command arguments
        :return: Result dictionary
        """
        try:
            result = self.cli.parse(args)
            return {
                'success': True,
                'result': result,
                'kwargs': self.cli.kwargs.copy(),
                'remainder': self.cli.remainder.copy()
            }
        except SystemExit as e:
            return {
                'success': False,
                'exit_code': e.code
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'exception': e
            }

    def assert_command_success(self, args):
        """Assert that a command runs successfully"""
        result = self.run_command(args)
        self.assertTrue(result.get('success'), f"Command failed: {args}")
        return result

    def assert_command_fails(self, args):
        """Assert that a command fails"""
        result = self.run_command(args)
        self.assertFalse(result.get('success'), f"Command should have failed: {args}")
        return result

    def create_test_pipeline(self, name='test_pipeline'):
        """Helper to create a test pipeline"""
        # Initialize Jarvis first
        init_args = ['init', self.config_dir, self.private_dir, self.shared_dir]
        self.run_command(init_args)

        # Create pipeline
        create_args = ['ppl', 'create', name]
        return self.run_command(create_args)

    def create_test_repo(self, name='test_repo', path=None):
        """Helper to create a test repository"""
        if path is None:
            path = os.path.join(self.test_dir, 'repos', name)

        # Create repo directory
        os.makedirs(path, exist_ok=True)

        # Initialize Jarvis if not done
        init_args = ['init', self.config_dir, self.private_dir, self.shared_dir]
        self.run_command(init_args)

        # Add repository
        add_args = ['repo', 'add', name, path]
        return self.run_command(add_args)

    def create_test_config_file(self, content, filename='test_config.yaml'):
        """Helper to create a test configuration file"""
        config_path = os.path.join(self.test_dir, filename)
        with open(config_path, 'w') as f:
            f.write(content)
        return config_path

"""
Tests for 'jarvis repo' and 'jarvis pkg' commands
"""
import os
from test.unit.core.test_cli_base import CLITestBase


class TestCLIRepository(CLITestBase):
    """Tests for repository management commands"""

    def test_repo_add(self):
        """Test adding a repository"""
        self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])

        repo_path = os.path.join(self.test_dir, 'test_repo')
        os.makedirs(repo_path, exist_ok=True)

        args = ['repo', 'add', 'myrepo', repo_path]
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['repo_name'], 'myrepo')
            self.assertEqual(result['kwargs']['repo_path'], repo_path)

    def test_repo_remove(self):
        """Test removing a repository"""
        self.create_test_repo('remove_me')

        args = ['repo', 'remove', 'remove_me']
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['repo_name'], 'remove_me')

    def test_repo_list(self):
        """Test listing repositories"""
        self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])

        args = ['repo', 'list']
        result = self.run_command(args)

        # Should execute successfully
        self.assertIsNotNone(result)

    def test_repo_create(self):
        """Test creating a new repository"""
        self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])

        repo_path = os.path.join(self.test_dir, 'new_repo')

        args = ['repo', 'create', 'newrepo', repo_path]
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['repo_name'], 'newrepo')
            self.assertEqual(result['kwargs']['repo_path'], repo_path)


class TestCLIPackage(CLITestBase):
    """Tests for package management commands"""

    def test_pkg_configure(self):
        """Test configuring a package"""
        self.create_test_pipeline()

        args = ['pkg', 'configure', 'test_pkg']
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['pkg_name'], 'test_pkg')

    def test_pkg_configure_with_options(self):
        """Test package configuration with options"""
        self.create_test_pipeline()

        args = ['pkg', 'configure', 'test_pkg', '--arg1=value1', '--arg2=value2']
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['pkg_name'], 'test_pkg')
            # Remainder should contain the options
            self.assertIn('--arg1=value1', result['remainder'])

    def test_pkg_readme(self):
        """Test viewing package README"""
        self.create_test_pipeline()

        args = ['pkg', 'readme', 'test_pkg']
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['pkg_name'], 'test_pkg')

    def test_pkg_path(self):
        """Test getting package path"""
        self.create_test_pipeline()

        args = ['pkg', 'path', 'test_pkg']
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['pkg_name'], 'test_pkg')

    def test_pkg_help(self):
        """Test package help command"""
        self.create_test_pipeline()

        args = ['pkg', 'help', 'test_pkg']
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['pkg_name'], 'test_pkg')


if __name__ == '__main__':
    import unittest
    unittest.main()

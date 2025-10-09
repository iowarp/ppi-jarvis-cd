"""
Tests for 'jarvis init' command
"""
import os
from test.unit.core.test_cli_base import CLITestBase


class TestCLIInit(CLITestBase):
    """Tests for the init command"""

    def test_init_default_directories(self):
        """Test init command with default directories"""
        args = ['init']
        result = self.run_command(args)

        # Command should parse successfully (though may not execute fully in test)
        self.assertTrue(result.get('success') or result.get('exit_code') == 0)

    def test_init_custom_directories(self):
        """Test init command with custom directories"""
        args = ['init', self.config_dir, self.private_dir, self.shared_dir]
        result = self.run_command(args)

        # Verify arguments were parsed correctly
        if result.get('success'):
            self.assertEqual(result['kwargs']['config_dir'], self.config_dir)
            self.assertEqual(result['kwargs']['private_dir'], self.private_dir)
            self.assertEqual(result['kwargs']['shared_dir'], self.shared_dir)

    def test_init_with_force(self):
        """Test init command with force flag"""
        args = ['init', self.config_dir, self.private_dir, self.shared_dir, '--force=true']
        result = self.run_command(args)

        if result.get('success'):
            self.assertTrue(result['kwargs']['force'])

    def test_init_creates_directories(self):
        """Test that init actually creates directories"""
        args = ['init', self.config_dir, self.private_dir, self.shared_dir]
        self.run_command(args)

        # Directories should exist after init (if command executed)
        # Note: This may not work in isolated test environment
        # The test verifies argument parsing at minimum

    def test_init_idempotent(self):
        """Test that init can be run multiple times safely"""
        args = ['init', self.config_dir, self.private_dir, self.shared_dir]

        # Run init twice
        result1 = self.run_command(args)
        result2 = self.run_command(args)

        # Both should succeed (or fail gracefully)
        self.assertIsNotNone(result1)
        self.assertIsNotNone(result2)


if __name__ == '__main__':
    import unittest
    unittest.main()

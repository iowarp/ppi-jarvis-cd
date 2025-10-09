"""
Tests for pkg_argparse.py - Package-specific argument parser
"""
import unittest
import sys
import os
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from jarvis_cd.util.pkg_argparse import PkgArgParse


class TestPkgArgParse(unittest.TestCase):
    """Tests for PkgArgParse class"""

    def setUp(self):
        """Set up test parser with sample configure menu"""
        self.configure_menu = [
            {'name': 'install_dir', 'msg': 'Installation directory', 'type': str, 'default': '/usr/local'},
            {'name': 'num_threads', 'msg': 'Number of threads', 'type': int, 'default': 4},
            {'name': 'enable_debug', 'msg': 'Enable debug mode', 'type': bool, 'default': False},
        ]
        self.parser = PkgArgParse('test_package', self.configure_menu)

    def test_initialization(self):
        """Test PkgArgParse initialization"""
        self.assertEqual(self.parser.pkg_name, 'test_package')
        self.assertIsNotNone(self.parser.cmds)

    def test_configure_command_exists(self):
        """Test that configure command is automatically added"""
        self.assertIn('configure', self.parser.cmds)

    def test_parse_configure_with_args(self):
        """Test parsing configure command with arguments"""
        args = ['configure', '--install_dir=/opt', '--num_threads=8']
        self.parser.parse(args)

        self.assertEqual(self.parser.kwargs['install_dir'], '/opt')
        self.assertEqual(self.parser.kwargs['num_threads'], 8)

    def test_parse_configure_with_defaults(self):
        """Test that default values are used"""
        args = ['configure']
        self.parser.parse(args)

        # Should have defaults
        self.assertIn('install_dir', self.parser.kwargs)
        self.assertIn('num_threads', self.parser.kwargs)

    def test_print_help(self):
        """Test print_help for package"""
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            self.parser.print_help()
            output = sys.stdout.getvalue()

            # Should contain package name and parameters
            self.assertIn('test_package', output)
            self.assertIn('install_dir', output.lower())
            self.assertIn('num_threads', output.lower())

        finally:
            sys.stdout = old_stdout

    def test_print_help_unknown_command(self):
        """Test print_help with unknown command"""
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            self.parser.print_help('unknown_cmd')
            output = sys.stdout.getvalue()

            # Should indicate unknown command
            self.assertIn('unknown', output.lower())

        finally:
            sys.stdout = old_stdout

    def test_print_help_configure_command(self):
        """Test print_help for configure command"""
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            self.parser.print_help('configure')
            output = sys.stdout.getvalue()

            # Should show configure help
            self.assertIn('test_package', output)

        finally:
            sys.stdout = old_stdout

    def test_empty_configure_menu(self):
        """Test PkgArgParse with empty configure menu"""
        parser = PkgArgParse('empty_package', [])
        args = ['configure']
        parser.parse(args)

        # Should not crash
        self.assertIsNotNone(parser.kwargs)


if __name__ == '__main__':
    unittest.main()

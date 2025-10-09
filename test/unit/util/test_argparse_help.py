"""
Tests for argparse help system
"""
import unittest
import sys
import os
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from jarvis_cd.util.argparse import ArgParse


class TestArgParseHelp(unittest.TestCase):
    """Tests for ArgParse help system"""

    def setUp(self):
        """Set up test parser"""
        self.parser = ArgParse()
        self.parser.add_menu('test', msg="Test menu")
        self.parser.add_cmd('test cmd1', msg="Test command 1")
        self.parser.add_args([
            {'name': 'arg1', 'msg': 'First argument', 'type': str, 'required': True, 'pos': True},
            {'name': 'arg2', 'msg': 'Second argument', 'type': int, 'default': 42}
        ])
        self.parser.add_cmd('test cmd2', msg="Test command 2")
        self.parser.add_args([
            {'name': 'flag', 'msg': 'Boolean flag', 'type': bool, 'default': False}
        ])

    def test_print_help_to_stdout(self):
        """Test that print_help outputs to stdout"""
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            self.parser.print_help()
            output = sys.stdout.getvalue()

            # Check output contains expected elements
            self.assertIn('test', output.lower())
            self.assertIn('cmd1', output.lower())
            self.assertIn('cmd2', output.lower())

        finally:
            sys.stdout = old_stdout

    def test_print_help_for_specific_command(self):
        """Test print_help for a specific command"""
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            self.parser.print_help('test cmd1')
            output = sys.stdout.getvalue()

            # Should contain command-specific help
            self.assertIn('arg1', output.lower())
            self.assertIn('first argument', output.lower())

        finally:
            sys.stdout = old_stdout

    def test_print_menu_help(self):
        """Test print_menu_help method"""
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            self.parser.print_menu_help('test')
            output = sys.stdout.getvalue()

            # Should contain menu help
            self.assertIn('test', output.lower())

        finally:
            sys.stdout = old_stdout

    def test_help_shows_required_args(self):
        """Test that help indicates required arguments"""
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            self.parser.print_help('test cmd1')
            output = sys.stdout.getvalue()

            # Should indicate arg1 is required
            self.assertIn('arg1', output.lower())
            self.assertIn('required', output.lower())

        finally:
            sys.stdout = old_stdout

    def test_help_shows_default_values(self):
        """Test that help shows default values"""
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            self.parser.print_help('test cmd1')
            output = sys.stdout.getvalue()

            # Should show default value for arg2
            self.assertIn('arg2', output.lower())
            self.assertIn('42', output)

        finally:
            sys.stdout = old_stdout

    def test_help_with_no_commands(self):
        """Test help when no commands are defined"""
        empty_parser = ArgParse()
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            empty_parser.print_help()
            output = sys.stdout.getvalue()

            # Should not crash
            self.assertIsInstance(output, str)

        finally:
            sys.stdout = old_stdout


if __name__ == '__main__':
    unittest.main()

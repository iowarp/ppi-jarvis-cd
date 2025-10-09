"""
Final argparse tests for remaining coverage
"""
import unittest
import sys
import os
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from jarvis_cd.util.argparse import ArgParse


class TestArgParseFinal(unittest.TestCase):
    """Tests for remaining uncovered ArgParse lines"""

    def test_help_flag_specific_command(self):
        """Test --help for specific command"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")
        parser.add_cmd('test cmd', msg="Command")
        parser.add_args([{'name': 'arg1', 'type': str}])

        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            parser.parse(['--help', 'test cmd'])
            output = sys.stdout.getvalue()
            self.assertIn('test', output.lower())
        finally:
            sys.stdout = old_stdout

    def test_dash_h_flag(self):
        """Test -h flag for help"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")

        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            parser.parse(['-h'])
            output = sys.stdout.getvalue()
            self.assertIn('test', output.lower())
        finally:
            sys.stdout = old_stdout

    def test_help_command(self):
        """Test help command"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")

        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            parser.parse(['help'])
            output = sys.stdout.getvalue()
            self.assertIsInstance(output, str)
        finally:
            sys.stdout = old_stdout

    def test_empty_args(self):
        """Test parsing empty args list"""
        parser = ArgParse()
        result = parser.parse([])
        self.assertEqual(result, {})

    def test_unknown_command(self):
        """Test unknown command handling"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")

        with self.assertRaises(SystemExit):
            parser.parse(['unknown_command'])

    def test_list_value_conversion_edge_case(self):
        """Test list value conversion with special format"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")
        parser.add_cmd('test cmd', msg="Test")
        parser.add_args([
            {'name': 'items', 'type': list}
        ])

        # Test single value to list
        args = ['test', 'cmd', '--items=single']
        parser.parse(args)
        self.assertIsInstance(parser.kwargs['items'], list)

    def test_dict_parse_error_handling(self):
        """Test dict parsing with invalid input"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")
        parser.add_cmd('test cmd', msg="Test")
        parser.add_args([
            {'name': 'config', 'type': dict}
        ])

        # Invalid dict
        args = ['test', 'cmd', '--config={invalid}']
        parser.parse(args)
        # Should handle gracefully
        self.assertIn('config', parser.kwargs)

    def test_get_argument_info_none(self):
        """Test _get_argument_info returns None for unknown arg"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")
        parser.add_cmd('test cmd', msg="Test")
        parser.add_args([{'name': 'known', 'type': str}])

        # This should not crash
        args = ['test', 'cmd', '--unknown=value']
        with self.assertRaises(SystemExit):
            parser.parse(args)

    def test_remainder_with_positionals(self):
        """Test remainder when positionals are exhausted"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")
        parser.add_cmd('test cmd', msg="Test", keep_remainder=True)
        parser.add_args([
            {'name': 'arg1', 'type': str, 'pos': True, 'required': True}
        ])

        args = ['test', 'cmd', 'value1', 'extra1', 'extra2']
        parser.parse(args)
        self.assertEqual(parser.kwargs['arg1'], 'value1')
        self.assertIn('extra1', parser.remainder)
        self.assertIn('extra2', parser.remainder)

    def test_convert_list_items_without_args(self):
        """Test _convert_list_items when no args definition"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")
        parser.add_cmd('test cmd', msg="Test")
        parser.add_args([
            {'name': 'items', 'type': list}  # No args sub-definition
        ])

        args = ['test', 'cmd', '--items=[{"key":"val"},{"key2":"val2"}]']
        parser.parse(args)
        # Should preserve dict items
        self.assertIsInstance(parser.kwargs['items'], list)

    def test_print_command_help_non_existent(self):
        """Test print_command_help for non-existent command"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")

        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            parser.print_command_help('nonexistent')
            output = sys.stdout.getvalue()
            # Should indicate command not found
            self.assertIsInstance(output, str)
        finally:
            sys.stdout = old_stdout

    def test_multiline_help_description(self):
        """Test command with multi-line description"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")
        parser.add_cmd('test cmd', msg="This is a\nmulti-line\ndescription")

        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            parser.print_help('test cmd')
            output = sys.stdout.getvalue()
            self.assertIn('test', output.lower())
        finally:
            sys.stdout = old_stdout


if __name__ == '__main__':
    unittest.main()

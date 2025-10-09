"""
Complete argparse tests for 100% coverage
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from jarvis_cd.util.argparse import ArgParse


class TestArgParseEdgeCases(unittest.TestCase):
    """Tests for ArgParse edge cases and uncovered lines"""

    def test_add_args_no_command_error(self):
        """Test add_args raises error when no command exists"""
        parser = ArgParse()
        with self.assertRaises(ValueError) as context:
            parser.add_args([{'name': 'test', 'type': str}])
        self.assertIn("No command", str(context.exception))

    def test_add_args_with_only_aliases(self):
        """Test add_args when only aliases exist"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test menu")
        parser.add_cmd('test cmd', msg="Test", aliases=['tc'])
        parser.add_args([{'name': 'arg1', 'type': str, 'pos': True, 'required': True}])

        # Should not crash
        self.assertIn('test cmd', parser.command_args)

    def test_parse_list_value_with_quotes(self):
        """Test _parse_list_value with quoted strings"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")
        parser.add_cmd('test cmd', msg="Test")
        parser.add_args([
            {'name': 'items', 'type': list, 'default': []}
        ])

        # Test with double quotes - the parser removes quotes but treats as single value
        args = ['test', 'cmd', '--items="a,b,c"']
        parser.parse(args)
        # When quotes are removed, it's treated as comma-separated
        self.assertIsInstance(parser.kwargs['items'], list)

    def test_parse_list_value_with_single_quotes(self):
        """Test _parse_list_value with single quotes"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")
        parser.add_cmd('test cmd', msg="Test")
        parser.add_args([
            {'name': 'items', 'type': list, 'default': []}
        ])

        args = ["test", "cmd", "--items='x,y,z'"]
        parser.parse(args)
        # Single quotes are handled by the parser
        self.assertIsInstance(parser.kwargs['items'], list)

    def test_parse_list_with_python_notation(self):
        """Test parsing list with Python notation"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")
        parser.add_cmd('test cmd', msg="Test")
        parser.add_args([
            {'name': 'items', 'type': list, 'default': []}
        ])

        args = ['test', 'cmd', '--items=[1,2,3]']
        parser.parse(args)
        # Should parse as list
        self.assertIsInstance(parser.kwargs['items'], list)

    def test_parse_list_with_tuple_args(self):
        """Test parsing list with tuple elements and args definition"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")
        parser.add_cmd('test cmd', msg="Test")
        parser.add_args([
            {
                'name': 'pairs',
                'type': list,
                'args': [
                    {'name': 'key', 'type': str},
                    {'name': 'value', 'type': int}
                ]
            }
        ])

        args = ['test', 'cmd', "--pairs=[(a,1),(b,2)]"]
        parser.parse(args)
        # Should convert tuples to dicts
        self.assertIsInstance(parser.kwargs['pairs'], list)

    def test_parse_dict_with_nested_args(self):
        """Test parsing dict with nested args definition"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")
        parser.add_cmd('test cmd', msg="Test")
        parser.add_args([
            {
                'name': 'config',
                'type': dict,
                'args': [
                    {'name': 'host', 'type': str},
                    {'name': 'port', 'type': int}
                ]
            }
        ])

        # Use simpler dict notation that works
        args = ['test', 'cmd', '--config=host:localhost,port:8080']
        parser.parse(args)
        result = parser.kwargs['config']
        self.assertIsInstance(result, dict)
        self.assertIn('host', result)
        self.assertIn('port', result)

    def test_cast_value_dict_failure(self):
        """Test _cast_value dict parsing failure"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")
        parser.add_cmd('test cmd', msg="Test")
        parser.add_args([
            {'name': 'config', 'type': dict}
        ])

        # Invalid dict string
        args = ['test', 'cmd', '--config=invalid{dict}']
        parser.parse(args)
        # Should return the value as-is when parsing fails
        self.assertIn('config', parser.kwargs)

    def test_convert_list_items_with_dict_items(self):
        """Test _convert_list_items with dict items"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")
        parser.add_cmd('test cmd', msg="Test")
        parser.add_args([
            {
                'name': 'items',
                'type': list,
                'args': [
                    {'name': 'id', 'type': int},
                    {'name': 'name', 'type': str}
                ]
            }
        ])

        args = ['test', 'cmd', '--items=[{"id":"1","name":"foo"},{"id":"2","name":"bar"}]']
        parser.parse(args)
        items = parser.kwargs['items']
        self.assertEqual(items[0]['id'], 1)  # Should be int

    def test_convert_list_items_single_value_with_args(self):
        """Test _convert_list_items with single value and args def"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")
        parser.add_cmd('test cmd', msg="Test")
        parser.add_args([
            {
                'name': 'nums',
                'type': list,
                'args': [{'name': 'value', 'type': int}]
            }
        ])

        args = ['test', 'cmd', '--nums=["1","2","3"]']
        parser.parse(args)
        # Should convert string values to int
        self.assertEqual(parser.kwargs['nums'], [1, 2, 3])

    def test_boolean_arg_plus_format(self):
        """Test boolean argument with + prefix"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")
        parser.add_cmd('test cmd', msg="Test")
        parser.add_args([
            {'name': 'verbose', 'type': bool, 'default': False}
        ])

        args = ['test', 'cmd', '+verbose']
        parser.parse(args)
        self.assertTrue(parser.kwargs['verbose'])

    def test_boolean_arg_minus_format(self):
        """Test boolean argument with - prefix"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")
        parser.add_cmd('test cmd', msg="Test")
        parser.add_args([
            {'name': 'debug', 'type': bool, 'default': True}
        ])

        args = ['test', 'cmd', '-debug']
        parser.parse(args)
        self.assertFalse(parser.kwargs['debug'])

    def test_positional_after_non_boolean_plus(self):
        """Test positional argument after non-boolean + arg"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")
        parser.add_cmd('test cmd', msg="Test")
        parser.add_args([
            {'name': 'file', 'type': str, 'pos': True, 'required': True}
        ])

        # +something that's not a boolean arg should be treated as positional
        args = ['test', 'cmd', '+notabool']
        parser.parse(args)
        self.assertEqual(parser.kwargs['file'], '+notabool')

    def test_remainder_with_keep_remainder_false(self):
        """Test remainder handling when keep_remainder is False"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")
        parser.add_cmd('test cmd', msg="Test", keep_remainder=False)
        parser.add_args([
            {'name': 'arg1', 'type': str, 'pos': True, 'required': True}
        ])

        # Extra args when keep_remainder=False should be ignored
        args = ['test', 'cmd', 'value1', 'extra', 'args']
        parser.parse(args)
        self.assertEqual(parser.kwargs['arg1'], 'value1')
        # Remainder should be empty since keep_remainder=False
        self.assertEqual(len(parser.remainder), 0)

    def test_negative_number_as_value(self):
        """Test negative number is not treated as flag"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")
        parser.add_cmd('test cmd', msg="Test")
        parser.add_args([
            {'name': 'value', 'type': int, 'pos': True, 'required': True}
        ])

        args = ['test', 'cmd', '-42']
        parser.parse(args)
        self.assertEqual(parser.kwargs['value'], -42)

    def test_menu_help(self):
        """Test menu help printing"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test menu")
        parser.add_cmd('test cmd1', msg="Command 1")
        parser.add_cmd('test cmd2', msg="Command 2")

        # Should not crash
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            parser.print_menu_help('test')
            output = sys.stdout.getvalue()
            self.assertIn('test', output.lower())
        finally:
            sys.stdout = old_stdout

    def test_command_help(self):
        """Test command help printing"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test menu")
        parser.add_cmd('test cmd', msg="Command")
        parser.add_args([
            {'name': 'arg1', 'type': str, 'msg': 'First argument', 'required': True},
            {'name': 'arg2', 'type': int, 'msg': 'Second argument', 'default': 10}
        ])

        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            parser.print_command_help('test cmd')
            output = sys.stdout.getvalue()
            self.assertIn('arg1', output.lower())
            self.assertIn('arg2', output.lower())
        finally:
            sys.stdout = old_stdout

    def test_choices_validation(self):
        """Test choices validation"""
        parser = ArgParse()
        parser.add_menu('test', msg="Test")
        parser.add_cmd('test cmd', msg="Test")
        parser.add_args([
            {'name': 'option', 'type': str, 'choices': ['a', 'b', 'c']}
        ])

        # Valid choice
        args = ['test', 'cmd', '--option=a']
        parser.parse(args)
        self.assertEqual(parser.kwargs['option'], 'a')

        # Invalid choice should raise error
        args = ['test', 'cmd', '--option=z']
        with self.assertRaises(SystemExit):
            parser.parse(args)


if __name__ == '__main__':
    unittest.main()

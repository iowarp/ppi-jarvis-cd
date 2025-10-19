import unittest
import sys
import os

# Add the project root to the path so we can import jarvis_cd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from jarvis_cd.util.argparse import ArgParse


class ComprehensiveArgParse(ArgParse):
    def define_options(self):
        # Test command with all type conversions
        self.add_menu('test', msg="Test menu")
        self.add_cmd('test types', msg="Test type conversions")
        self.add_args([
            {'name': 'str_arg', 'type': str, 'default': 'default_str'},
            {'name': 'int_arg', 'type': int, 'default': 0},
            {'name': 'float_arg', 'type': float, 'default': 0.0},
            {'name': 'bool_arg', 'type': bool, 'default': False},
            {'name': 'list_arg', 'type': list, 'default': []},
            {'name': 'dict_arg', 'type': dict, 'default': {}},
        ])

        # Test command with required arguments
        self.add_cmd('test required', msg="Test required arguments")
        self.add_args([
            {'name': 'required_str', 'type': str, 'required': True},
            {'name': 'required_int', 'type': int, 'required': True},
            {'name': 'optional_str', 'type': str, 'default': 'optional'},
        ])

        # Test command with remainder arguments
        self.add_cmd('test remainder', msg="Test remainder arguments", keep_remainder=True)
        self.add_args([
            {'name': 'first_arg', 'type': str, 'pos': True},
        ])

        # Test command with list of dictionaries
        self.add_cmd('test listdict', msg="Test list of dictionaries")
        self.add_args([
            {
                'name': 'items',
                'type': list,
                'args': [
                    {'name': 'name', 'type': str},
                    {'name': 'value', 'type': int},
                    {'name': 'enabled', 'type': bool}
                ]
            }
        ])

        # Test command with positional arguments
        self.add_cmd('test positional', msg="Test positional arguments")
        self.add_args([
            {'name': 'pos1', 'type': str, 'pos': True, 'required': True},
            {'name': 'pos2', 'type': int, 'pos': True, 'required': True},
            {'name': 'pos3', 'type': float, 'pos': True, 'default': 3.14},
        ])

        # Test command with no remainder (should reject undefined args)
        self.add_cmd('test strict', msg="Test strict argument checking", keep_remainder=False)
        self.add_args([
            {'name': 'known_arg', 'type': str},
        ])

        # Test command with dict argument
        self.add_cmd('test dict', msg="Test dict argument")
        self.add_args([
            {
                'name': 'config',
                'type': dict,
                'args': [
                    {'name': 'host', 'type': str},
                    {'name': 'port', 'type': int},
                ]
            }
        ])

        # Test command with choices
        self.add_cmd('test choices', msg="Test argument with choices")
        self.add_args([
            {'name': 'mode', 'type': str, 'choices': ['read', 'write', 'append'], 'required': True},
        ])

        # Test boolean flags
        self.add_cmd('test bool', msg="Test boolean flags")
        self.add_args([
            {'name': 'flag1', 'type': bool, 'default': False},
            {'name': 'flag2', 'type': bool, 'default': True},
        ])

    def test_types(self):
        pass

    def test_required(self):
        pass

    def test_remainder(self):
        pass

    def test_listdict(self):
        pass

    def test_positional(self):
        pass

    def test_strict(self):
        pass

    def test_dict(self):
        pass

    def test_choices(self):
        pass

    def test_bool(self):
        pass


class TestArgParseTypeConversions(unittest.TestCase):

    def setUp(self):
        self.parser = ComprehensiveArgParse()
        self.parser.define_options()

    def test_str_conversion(self):
        """Test string type conversion"""
        args = ['test', 'types', '--str_arg=hello']
        result = self.parser.parse(args)

        self.assertEqual(self.parser.kwargs['str_arg'], 'hello')
        self.assertIsInstance(self.parser.kwargs['str_arg'], str)

    def test_int_conversion(self):
        """Test int type conversion"""
        args = ['test', 'types', '--int_arg=42']
        result = self.parser.parse(args)

        self.assertEqual(self.parser.kwargs['int_arg'], 42)
        self.assertIsInstance(self.parser.kwargs['int_arg'], int)

    def test_float_conversion(self):
        """Test float type conversion"""
        args = ['test', 'types', '--float_arg=3.14159']
        result = self.parser.parse(args)

        self.assertAlmostEqual(self.parser.kwargs['float_arg'], 3.14159)
        self.assertIsInstance(self.parser.kwargs['float_arg'], float)

    def test_bool_conversion_true(self):
        """Test bool type conversion to True"""
        args = ['test', 'types', '--bool_arg=true']
        result = self.parser.parse(args)

        self.assertEqual(self.parser.kwargs['bool_arg'], True)
        self.assertIsInstance(self.parser.kwargs['bool_arg'], bool)

    def test_bool_conversion_false(self):
        """Test bool type conversion to False"""
        args = ['test', 'types', '--bool_arg=false']
        result = self.parser.parse(args)

        self.assertEqual(self.parser.kwargs['bool_arg'], False)
        self.assertIsInstance(self.parser.kwargs['bool_arg'], bool)

    def test_list_conversion(self):
        """Test list type conversion"""
        args = ['test', 'types', '--list_arg=["item1", "item2", "item3"]']
        result = self.parser.parse(args)

        self.assertEqual(self.parser.kwargs['list_arg'], ["item1", "item2", "item3"])
        self.assertIsInstance(self.parser.kwargs['list_arg'], list)

    def test_dict_conversion(self):
        """Test dict type conversion"""
        args = ['test', 'types', '--dict_arg={"key1": "value1", "key2": 42}']
        result = self.parser.parse(args)

        self.assertEqual(self.parser.kwargs['dict_arg'], {"key1": "value1", "key2": 42})
        self.assertIsInstance(self.parser.kwargs['dict_arg'], dict)

    def test_int_from_numeric_string(self):
        """Test int conversion from numeric string"""
        args = ['test', 'types', '--int_arg', '123']
        result = self.parser.parse(args)

        self.assertEqual(self.parser.kwargs['int_arg'], 123)

    def test_float_from_numeric_string(self):
        """Test float conversion from numeric string"""
        args = ['test', 'types', '--float_arg', '2.718']
        result = self.parser.parse(args)

        self.assertAlmostEqual(self.parser.kwargs['float_arg'], 2.718)

    def test_negative_int(self):
        """Test negative integer conversion"""
        args = ['test', 'types', '--int_arg=-42']
        result = self.parser.parse(args)

        self.assertEqual(self.parser.kwargs['int_arg'], -42)

    def test_negative_float(self):
        """Test negative float conversion"""
        args = ['test', 'types', '--float_arg=-3.14']
        result = self.parser.parse(args)

        self.assertAlmostEqual(self.parser.kwargs['float_arg'], -3.14)


class TestArgParseRequiredArguments(unittest.TestCase):

    def setUp(self):
        self.parser = ComprehensiveArgParse()
        self.parser.define_options()

    def test_required_arguments_provided(self):
        """Test that required arguments are accepted when provided"""
        args = ['test', 'required', '--required_str=hello', '--required_int=42']
        result = self.parser.parse(args)

        self.assertEqual(self.parser.kwargs['required_str'], 'hello')
        self.assertEqual(self.parser.kwargs['required_int'], 42)
        self.assertEqual(self.parser.kwargs['optional_str'], 'optional')

    def test_required_str_missing(self):
        """Test that missing required string argument raises error"""
        args = ['test', 'required', '--required_int=42']

        with self.assertRaises(SystemExit):
            self.parser.parse(args)

    def test_required_int_missing(self):
        """Test that missing required int argument raises error"""
        args = ['test', 'required', '--required_str=hello']

        with self.assertRaises(SystemExit):
            self.parser.parse(args)

    def test_all_required_missing(self):
        """Test that all missing required arguments raise error"""
        args = ['test', 'required']

        with self.assertRaises(SystemExit):
            self.parser.parse(args)

    def test_optional_can_be_omitted(self):
        """Test that optional arguments can be omitted"""
        args = ['test', 'required', '--required_str=hello', '--required_int=42']
        result = self.parser.parse(args)

        self.assertEqual(self.parser.kwargs['optional_str'], 'optional')


class TestArgParseRemainderArguments(unittest.TestCase):

    def setUp(self):
        self.parser = ComprehensiveArgParse()
        self.parser.define_options()

    def test_remainder_arguments_collected(self):
        """Test that remainder arguments are collected"""
        args = ['test', 'remainder', 'first', 'extra1', 'extra2', 'extra3']
        result = self.parser.parse(args)

        self.assertEqual(self.parser.kwargs['first_arg'], 'first')
        self.assertEqual(self.parser.remainder, ['extra1', 'extra2', 'extra3'])

    def test_remainder_with_no_extras(self):
        """Test remainder when no extra arguments provided"""
        args = ['test', 'remainder', 'first']
        result = self.parser.parse(args)

        self.assertEqual(self.parser.kwargs['first_arg'], 'first')
        self.assertEqual(self.parser.remainder, [])

    def test_undefined_args_without_remainder(self):
        """Test that undefined arguments without keep_remainder raise an error"""
        args = ['test', 'strict', '--known_arg=value', '--unknown_arg=bad']

        # The command is marked as strict (keep_remainder=False), so undefined args should raise error
        # This matches the command definition comment: "should reject undefined args"
        with self.assertRaises(SystemExit):
            self.parser.parse(args)


class TestArgParseListArguments(unittest.TestCase):

    def setUp(self):
        self.parser = ComprehensiveArgParse()
        self.parser.define_options()

    def test_list_of_dicts_set_mode(self):
        """Test list of dictionaries in set mode"""
        args = ['test', 'listdict', '--items=[("item1", 10, True), ("item2", 20, False)]']
        result = self.parser.parse(args)

        expected = [
            {'name': 'item1', 'value': 10, 'enabled': True},
            {'name': 'item2', 'value': 20, 'enabled': False}
        ]
        self.assertEqual(self.parser.kwargs['items'], expected)

    def test_list_of_dicts_append_mode(self):
        """Test list of dictionaries in append mode"""
        args = ['test', 'listdict', '--items', '("item1", 10, True)', '--items', '("item2", 20, False)']
        result = self.parser.parse(args)

        expected = [
            {'name': 'item1', 'value': 10, 'enabled': True},
            {'name': 'item2', 'value': 20, 'enabled': False}
        ]
        self.assertEqual(self.parser.kwargs['items'], expected)

    def test_empty_list_default(self):
        """Test empty list default value"""
        args = ['test', 'types']
        result = self.parser.parse(args)

        self.assertEqual(self.parser.kwargs['list_arg'], [])

    def test_list_type_conversion(self):
        """Test that list items are converted to proper types"""
        args = ['test', 'listdict', '--items=[("test", 123, True)]']
        result = self.parser.parse(args)

        item = self.parser.kwargs['items'][0]
        self.assertIsInstance(item['name'], str)
        self.assertIsInstance(item['value'], int)
        self.assertIsInstance(item['enabled'], bool)


class TestArgParseDictArguments(unittest.TestCase):

    def setUp(self):
        self.parser = ComprehensiveArgParse()
        self.parser.define_options()

    def test_dict_argument(self):
        """Test dict argument parsing"""
        args = ['test', 'dict', '--config={"host": "localhost", "port": 8080}']
        result = self.parser.parse(args)

        self.assertEqual(self.parser.kwargs['config']['host'], 'localhost')
        self.assertEqual(self.parser.kwargs['config']['port'], 8080)

    def test_dict_type_conversion(self):
        """Test that dict values are converted to proper types"""
        args = ['test', 'dict', '--config={"host": "server.com", "port": 443}']
        result = self.parser.parse(args)

        config = self.parser.kwargs['config']
        self.assertIsInstance(config['host'], str)
        self.assertIsInstance(config['port'], int)


class TestArgParsePositionalArguments(unittest.TestCase):

    def setUp(self):
        self.parser = ComprehensiveArgParse()
        self.parser.define_options()

    def test_positional_arguments_order(self):
        """Test that positional arguments are parsed in order"""
        args = ['test', 'positional', 'hello', '42', '2.718']
        result = self.parser.parse(args)

        self.assertEqual(self.parser.kwargs['pos1'], 'hello')
        self.assertEqual(self.parser.kwargs['pos2'], 42)
        self.assertAlmostEqual(self.parser.kwargs['pos3'], 2.718)

    def test_positional_with_defaults(self):
        """Test positional arguments with defaults"""
        args = ['test', 'positional', 'hello', '42']
        result = self.parser.parse(args)

        self.assertEqual(self.parser.kwargs['pos1'], 'hello')
        self.assertEqual(self.parser.kwargs['pos2'], 42)
        self.assertAlmostEqual(self.parser.kwargs['pos3'], 3.14)

    def test_positional_required_missing(self):
        """Test that missing required positional argument raises error"""
        args = ['test', 'positional', 'hello']

        with self.assertRaises(SystemExit):
            self.parser.parse(args)

    def test_positional_type_conversion(self):
        """Test type conversion for positional arguments"""
        args = ['test', 'positional', 'test', '100', '1.5']
        result = self.parser.parse(args)

        self.assertIsInstance(self.parser.kwargs['pos1'], str)
        self.assertIsInstance(self.parser.kwargs['pos2'], int)
        self.assertIsInstance(self.parser.kwargs['pos3'], float)


class TestArgParseChoices(unittest.TestCase):

    def setUp(self):
        self.parser = ComprehensiveArgParse()
        self.parser.define_options()

    def test_valid_choice(self):
        """Test that valid choice is accepted"""
        args = ['test', 'choices', '--mode=read']
        result = self.parser.parse(args)

        self.assertEqual(self.parser.kwargs['mode'], 'read')

    def test_invalid_choice(self):
        """Test that invalid choice raises error"""
        args = ['test', 'choices', '--mode=execute']

        with self.assertRaises(SystemExit):
            self.parser.parse(args)

    def test_all_valid_choices(self):
        """Test all valid choices"""
        for mode in ['read', 'write', 'append']:
            self.parser = ComprehensiveArgParse()
            self.parser.define_options()
            args = ['test', 'choices', f'--mode={mode}']
            result = self.parser.parse(args)
            self.assertEqual(self.parser.kwargs['mode'], mode)


class TestArgParseBooleanFlags(unittest.TestCase):

    def setUp(self):
        self.parser = ComprehensiveArgParse()
        self.parser.define_options()

    def test_plus_flag_sets_true(self):
        """Test +flag sets boolean to true"""
        args = ['test', 'bool', '+flag1']
        result = self.parser.parse(args)

        self.assertEqual(self.parser.kwargs['flag1'], True)

    def test_minus_flag_sets_false(self):
        """Test -flag sets boolean to false"""
        args = ['test', 'bool', '-flag2']
        result = self.parser.parse(args)

        self.assertEqual(self.parser.kwargs['flag2'], False)

    def test_bool_keyword_true(self):
        """Test boolean keyword argument set to true"""
        args = ['test', 'bool', '--flag1=true']
        result = self.parser.parse(args)

        self.assertEqual(self.parser.kwargs['flag1'], True)

    def test_bool_keyword_false(self):
        """Test boolean keyword argument set to false"""
        args = ['test', 'bool', '--flag1=false']
        result = self.parser.parse(args)

        self.assertEqual(self.parser.kwargs['flag1'], False)

    def test_bool_variations(self):
        """Test various boolean value representations"""
        true_values = ['true', 'True', '1', 'yes', 'on']
        for val in true_values:
            self.parser = ComprehensiveArgParse()
            self.parser.define_options()
            args = ['test', 'bool', f'--flag1={val}']
            result = self.parser.parse(args)
            self.assertEqual(self.parser.kwargs['flag1'], True, f"Failed for value: {val}")


class TestArgParseDictMode(unittest.TestCase):

    def setUp(self):
        self.parser = ComprehensiveArgParse()
        self.parser.define_options()

    def test_parse_dict_basic(self):
        """Test parse_dict with basic types"""
        arg_dict = {
            'str_arg': 'hello',
            'int_arg': 42,
            'float_arg': 3.14,
            'bool_arg': True
        }
        result = self.parser.parse_dict('test types', arg_dict)

        self.assertEqual(self.parser.kwargs['str_arg'], 'hello')
        self.assertEqual(self.parser.kwargs['int_arg'], 42)
        self.assertAlmostEqual(self.parser.kwargs['float_arg'], 3.14)
        self.assertEqual(self.parser.kwargs['bool_arg'], True)

    def test_parse_dict_type_conversion(self):
        """Test parse_dict performs type conversion"""
        arg_dict = {
            'int_arg': '123',  # String that should be converted to int
            'float_arg': '2.5',  # String that should be converted to float
        }
        result = self.parser.parse_dict('test types', arg_dict)

        self.assertEqual(self.parser.kwargs['int_arg'], 123)
        self.assertIsInstance(self.parser.kwargs['int_arg'], int)
        self.assertAlmostEqual(self.parser.kwargs['float_arg'], 2.5)
        self.assertIsInstance(self.parser.kwargs['float_arg'], float)

    def test_parse_dict_with_list(self):
        """Test parse_dict with list argument"""
        arg_dict = {
            'items': [
                ('item1', 10, True),
                ('item2', 20, False)
            ]
        }
        result = self.parser.parse_dict('test listdict', arg_dict)

        expected = [
            {'name': 'item1', 'value': 10, 'enabled': True},
            {'name': 'item2', 'value': 20, 'enabled': False}
        ]
        self.assertEqual(self.parser.kwargs['items'], expected)

    def test_parse_dict_required_args(self):
        """Test parse_dict validates required arguments"""
        arg_dict = {
            'required_str': 'hello'
            # Missing required_int
        }

        with self.assertRaises(SystemExit):
            self.parser.parse_dict('test required', arg_dict)

    def test_parse_dict_with_defaults(self):
        """Test parse_dict uses default values"""
        arg_dict = {}
        result = self.parser.parse_dict('test types', arg_dict)

        self.assertEqual(self.parser.kwargs['str_arg'], 'default_str')
        self.assertEqual(self.parser.kwargs['int_arg'], 0)
        self.assertEqual(self.parser.kwargs['float_arg'], 0.0)
        self.assertEqual(self.parser.kwargs['bool_arg'], False)


if __name__ == '__main__':
    unittest.main()

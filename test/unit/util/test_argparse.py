import unittest
import sys
import os

# Add the project root to the path so we can import jarvis_cd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from jarvis_cd.util.argparse import ArgParse


class MyAppArgParse(ArgParse):
    def define_options(self):
        self.add_menu('')
        self.add_cmd('', keep_remainder=True)
        self.add_args([
            {
                'name': 'hi',
                'msg': 'hello',
                'type': str,
                'default': None
            }
        ])

        self.add_menu('vpic', msg="The VPIC application")
        self.add_cmd('vpic run',
                      keep_remainder=False,
                      aliases=['vpic r', 'vpic runner'])
        self.add_args([
            {
                'name': 'steps',
                'msg': 'Number of checkpoints',
                'type': int,
                'required': True,
                'pos': True,
                'class': 'sim',
                'rank': 0
            },
            {
                'name': 'x',
                'msg': 'The length of the x-axis',
                'type': int,
                'required': False,
                'default': 256,
                'pos': True,
                'class': 'sim',
                'rank': 1
            },
            {
                'name': 'do_io',
                'msg': 'Whether to perform I/O or not',
                'type': bool,
                'required': False,
                'default': False,
                'pos': True,
            },
            {
                'name': 'make_figures',
                'msg': 'Whether to make a figure',
                'type': bool,
                'default': False,
            },
            {
                'name': 'data_size',
                'msg': 'Total amount of data to produce',
                'type': int,
                'default': 1024,
            },
            {
                'name': 'hosts',
                'msg': 'A list of hosts',
                'type': list,
                'args': [
                    {
                        'name': 'host',
                        'msg': 'A string representing a host',
                        'type': str,
                    }
                ],
                'aliases': ['x']
            },
            {
                'name': 'devices',
                'msg': 'A list of devices and counts',
                'type': list,
                'aliases': ['d'],
                'args': [
                    {
                        'name': 'path',
                        'msg': 'The mount point of device',
                        'type': str,
                    },
                    {
                        'name': 'count',
                        'msg': 'The number of devices to search for',
                        'type': int,
                    }
                ]
            }
        ])

    def main_menu(self):
        pass
        
    def vpic_run(self):
        pass


class TestArgParse(unittest.TestCase):
    
    def setUp(self):
        self.parser = MyAppArgParse()
        self.parser.define_options()
    
    def test_empty_menu_with_remainder(self):
        """Test: my_app hi="hi" rem1 rem2 rem3"""
        args = ['hi=hi', 'rem1', 'rem2', 'rem3']
        result = self.parser.parse(args)
        
        self.assertEqual(self.parser.kwargs['hi'], 'hi')
        self.assertEqual(self.parser.remainder, ['rem1', 'rem2', 'rem3'])
    
    def test_vpic_run_basic(self):
        """Test basic vpic run command with required positional args"""
        args = ['vpic', 'run', '10']
        result = self.parser.parse(args)
        
        self.assertEqual(self.parser.kwargs['steps'], 10)
        self.assertEqual(self.parser.kwargs['x'], 256)  # default value
        self.assertEqual(self.parser.kwargs['do_io'], False)  # default value
        
    def test_vpic_run_with_positional_args(self):
        """Test vpic run with multiple positional arguments"""
        args = ['vpic', 'run', '10', '512', 'true']
        result = self.parser.parse(args)
        
        self.assertEqual(self.parser.kwargs['steps'], 10)
        self.assertEqual(self.parser.kwargs['x'], 512)
        self.assertEqual(self.parser.kwargs['do_io'], True)
        
    def test_vpic_run_with_keyword_args(self):
        """Test vpic run with keyword arguments"""
        args = ['vpic', 'run', '10', '--make_figures=true', '--data_size=2048']
        result = self.parser.parse(args)
        
        self.assertEqual(self.parser.kwargs['steps'], 10)
        self.assertEqual(self.parser.kwargs['make_figures'], True)
        self.assertEqual(self.parser.kwargs['data_size'], 2048)
        
    def test_list_args_set_mode(self):
        """Test: my_app vpic run 1 --devices="[(/mnt/home, 5), (/mnt/home2, 6)]" """
        args = ['vpic', 'run', '1', '--devices=[("/mnt/home", 5), ("/mnt/home2", 6)]']
        result = self.parser.parse(args)
        
        expected_devices = [
            {'path': '/mnt/home', 'count': 5},
            {'path': '/mnt/home2', 'count': 6}
        ]
        self.assertEqual(self.parser.kwargs['devices'], expected_devices)
        
    def test_list_args_append_mode(self):
        """Test: my_app vpic run 1 --d "(/mnt/home, 5)" --d "(/mnt/home2, 6)" """
        args = ['vpic', 'run', '1', '--d', '("/mnt/home", 5)', '--d', '("/mnt/home2", 6)']
        result = self.parser.parse(args)
        
        expected_devices = [
            {'path': '/mnt/home', 'count': 5},
            {'path': '/mnt/home2', 'count': 6}
        ]
        self.assertEqual(self.parser.kwargs['devices'], expected_devices)
        
    def test_short_options(self):
        """Test short option aliases"""
        args = ['vpic', 'run', '1', '-d', '("/mnt/home", 5)']
        result = self.parser.parse(args)
        
        expected_devices = [{'path': '/mnt/home', 'count': 5}]
        self.assertEqual(self.parser.kwargs['devices'], expected_devices)
        
    def test_command_aliases(self):
        """Test command aliases work"""
        args = ['vpic', 'r', '10']
        result = self.parser.parse(args)
        
        self.assertEqual(self.parser.kwargs['steps'], 10)
        
        # Test another alias
        args = ['vpic', 'runner', '20']
        result = self.parser.parse(args)
        
        self.assertEqual(self.parser.kwargs['steps'], 20)
        
    def test_required_argument_missing(self):
        """Test that missing required arguments raise an error"""
        args = ['vpic', 'run']  # missing required 'steps' argument

        with self.assertRaises(SystemExit):
            self.parser.parse(args)
        
    def test_type_casting(self):
        """Test various type casting"""
        args = ['vpic', 'run', '10', '512', 'false', '--make_figures=true', '--data_size=4096']
        result = self.parser.parse(args)
        
        self.assertEqual(type(self.parser.kwargs['steps']), int)
        self.assertEqual(type(self.parser.kwargs['x']), int)
        self.assertEqual(type(self.parser.kwargs['do_io']), bool)
        self.assertEqual(type(self.parser.kwargs['make_figures']), bool)
        self.assertEqual(type(self.parser.kwargs['data_size']), int)
        
        self.assertEqual(self.parser.kwargs['steps'], 10)
        self.assertEqual(self.parser.kwargs['x'], 512)
        self.assertEqual(self.parser.kwargs['do_io'], False)
        self.assertEqual(self.parser.kwargs['make_figures'], True)
        self.assertEqual(self.parser.kwargs['data_size'], 4096)
        
    def test_argument_ranking(self):
        """Test that arguments are processed in class/rank order"""
        args = ['vpic', 'run', '10', '512']
        result = self.parser.parse(args)
        
        # steps (class='sim', rank=0) should be filled first
        # x (class='sim', rank=1) should be filled second
        self.assertEqual(self.parser.kwargs['steps'], 10)
        self.assertEqual(self.parser.kwargs['x'], 512)
        
    def test_empty_command_defaults(self):
        """Test empty command with no arguments"""
        args = []
        result = self.parser.parse(args)
        
        # Should use default value for 'hi'
        self.assertEqual(self.parser.kwargs.get('hi'), None)
        self.assertEqual(self.parser.remainder, [])
        
    def test_invalid_menu_command(self):
        """Test behavior with invalid menu commands"""
        # This test might print error messages, but shouldn't crash
        args = ['vpic', 'invalid_command']
        result = self.parser.parse(args)
        
        # Should not crash and return empty kwargs
        self.assertEqual(result, {})


if __name__ == '__main__':
    unittest.main()
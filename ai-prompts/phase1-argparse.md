
## Argument Parsing

Put this in jarvis_cd.util as argparse.py. Implement this class and build a unit test.

We want to build a custom library for parsing arguments. It should support
positional, keyword, and remainder arguments.

### Argument structure

The argument parser should have the following concepts:
* menu: a set of commands
* command: has a name and a set of args
* args

### Argument dict
```python
{
    'name': 'name of argument'
    'msg': 'description of argument'
    'type': 'type to cast argument to'
    'default': 'default value'
    'class': 'string. the name of a group of commands.'
    'rank': 'integer. orders arguments within a class'
    'required': 'complain if message is required'
    'args': 'specific for list types. list of this dictionary. Defines the structure of the list'.
    'aliases': 'any alternative names for the argument'
}
```


### self.add_menu

This will add a new menu to parse. A menu contains commands. If the a command is not found in a menu, then the set of commands and their arguments should be printed as error.

It takes as input a name. The name is a space-separated string. Each word in the string indicates either a sub-menu or a command within a menu. For example, 

"vpic run"

Is considered a command in the below example, while "vpic" is considered a menu.

### self.add_cmd

Commands are attached to menus as they are defined. The full string including menu name should be used to identify this class.

### self.add_args

Arguments are attached to commands as they are defined. 

### Example

Here is the argument parsing class for a file named "my_app.py"
```python
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
                'aliases': ['d']
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
        self.kwargs # The dictionary built
        self.remainder # any remaining args 
    def vpic_run(self): pass 
```

### Example: Empty menu, empty cmd
```
my_app hi="hi" rem1 rem2 rem3
```

self.remainder will contain [rem1, rem2, rem3]

self.kwargs will contain 'hi'

### Example 2: Set list args
Set the list, replacing old values in the list:
```
my_app vpic run 1 --devices="[(/mnt/home, 5), (/mnt/home2, 6)]"
```

### Example 3: Append to list args
Append to the list, keeping the old values. Difference is the = sign is missing.
```
my_app vpic run 1 --d "(/mnt/home, 5)" --d "(/mnt/home2, 6)"
```

Same as example 2, but slightly different

### Example 4: Boolean
I would like booleans in the argparse to support +/-. 
```
vpic run +do_io
```
should set do_io to true. 

Alternatively
```
vpic run -do_io
```


Sets it to falsee

## Dictionary Arguments

Sometimes, we already have a dictionary of parameters for a particular command, but the individual parameters have not yet been converted to their final types. 

For example, let's say we have a configuration for ``vpic run``:
```
arg_dict = {
    'do_io': True,
    'devices': [
        ("path", "1"),
        ("path2", "2")
    ]
}
```

We should have an api as follows:
```
ArgParse.parse_dict('vpic run', arg_dict)
```

We do not have remainder support for this version, so it will only set self.kwargs

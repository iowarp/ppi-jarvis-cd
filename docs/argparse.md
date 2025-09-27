# ArgParse Class Documentation

## Overview

The `ArgParse` class is a custom argument parsing library designed to support complex command-line interfaces with menus, commands, and sophisticated argument handling. It provides an alternative to Python's built-in `argparse` module with enhanced support for positional arguments, argument ranking, and remainder handling.

## Location

```python
from jarvis_cd.util.argparse import ArgParse
```

## Class Hierarchy

```
ArgParse (base class)
├── Custom application parsers (inherit from ArgParse)
```

## Core Concepts

### Menu
A grouping of related commands. Menus can be nested and provide organization for command sets.

### Command
A specific action that can be executed, belonging to a menu. Commands have names and can have aliases.

### Arguments
Parameters that commands accept, supporting:
- **Positional arguments**: Ordered by class and rank
- **Keyword arguments**: Named parameters with `--` or `-` prefixes
- **Remainder arguments**: Catch-all for additional parameters

## Constructor

```python
def __init__(self):
    """
    Initialize the argument parser.
    Sets up internal data structures for menus, commands, and arguments.
    """
```

**Parameters**: None

**Attributes**:
- `menus`: Dictionary of defined menus
- `commands`: Dictionary of defined commands
- `command_args`: Dictionary mapping commands to their arguments
- `kwargs`: Parsed keyword arguments (populated after parsing)
- `remainder`: Remaining unparsed arguments (populated after parsing)

## Core Methods

### define_options()

```python
def define_options(self):
    """
    Override this method to define your command structure.
    Called during initialization to set up menus, commands, and arguments.
    """
```

**Purpose**: Must be overridden in subclasses to define the argument structure.

### add_menu()

```python
def add_menu(self, name: str, msg: str = ""):
    """
    Add a menu to the parser.
    
    :param name: Space-separated menu path (e.g., "vpic" or "app subcommand")
    :param msg: Description of the menu
    """
```

**Parameters**:
- `name` (str): Menu identifier. Space-separated for nested menus
- `msg` (str, optional): Human-readable description

**Example**:
```python
self.add_menu('', msg="Main menu")
self.add_menu('vpic', msg="VPIC simulation commands")
```

### add_cmd()

```python
def add_cmd(self, name: str, keep_remainder: bool = False, aliases: Optional[List[str]] = None):
    """
    Add a command to a menu.
    
    :param name: Full command name including menu (e.g., "vpic run")
    :param keep_remainder: Whether to collect unparsed arguments in self.remainder
    :param aliases: Alternative command names
    """
```

**Parameters**:
- `name` (str): Full command path (menu + command name)
- `keep_remainder` (bool): If True, unparsed args go to `self.remainder`
- `aliases` (List[str], optional): Alternative command names

**Example**:
```python
self.add_cmd('vpic run', keep_remainder=False, aliases=['vpic r', 'vpic runner'])
```

### add_args()

```python
def add_args(self, args_list: List[Dict[str, Any]]):
    """
    Add arguments to the most recently added command.
    
    :param args_list: List of argument dictionaries
    """
```

**Parameters**:
- `args_list` (List[Dict]): List of argument specifications

**Argument Dictionary Structure**:
```python
{
    'name': str,           # Argument name
    'msg': str,            # Description
    'type': type,          # Type to cast to (str, int, bool, list)
    'default': Any,        # Default value
    'class': str,          # Grouping class for positional ordering
    'rank': int,           # Order within class
    'required': bool,      # Whether argument is mandatory
    'pos': bool,           # Whether it's a positional argument
    'aliases': List[str],  # Alternative names
    'args': List[Dict],    # For list types: structure of list items
}
```

### parse()

```python
def parse(self, args: List[str]) -> Dict[str, Any]:
    """
    Parse command line arguments.
    
    :param args: List of command line arguments
    :return: Dictionary of parsed arguments
    """
```

**Parameters**:
- `args` (List[str]): Command-line arguments to parse

**Returns**:
- `Dict[str, Any]`: Parsed arguments accessible via `self.kwargs`

**Side Effects**:
- Populates `self.kwargs` with parsed arguments
- Populates `self.remainder` with unparsed arguments
- Calls appropriate command handler method

## Utility Methods

### subset()
```python
def subset(self, count: int, path: Optional[str] = None) -> 'Hostfile'
```

### copy()
```python
def copy(self) -> 'Hostfile'
```

## Argument Types and Parsing

### Positional Arguments
Arguments with `'pos': True` are parsed in order determined by:
1. `'class'` field (alphabetically)
2. `'rank'` field (numerically)
3. Arguments without class come last

### Keyword Arguments
- Long form: `--argument=value` or `--argument value`
- Short form: `-a value`
- Aliases supported for argument names

### List Arguments
Special handling for `'type': list`:

**Set Mode** (with `=`):
```bash
--devices="[(/mnt/home, 5), (/mnt/home2, 6)]"
```

**Append Mode** (without `=`):
```bash
--d "(/mnt/home, 5)" --d "(/mnt/home2, 6)"
```

### Type Casting
Automatic conversion based on `'type'` field:
- `str`: String conversion
- `int`: Integer conversion
- `bool`: Boolean conversion (`'true'`, `'1'`, `'yes'`, `'on'` → True)
- `list`: Special list parsing

## Example Implementation

```python
class MyAppArgParse(ArgParse):
    def define_options(self):
        # Main menu with remainder collection
        self.add_menu('')
        self.add_cmd('', keep_remainder=True)
        self.add_args([
            {
                'name': 'verbose',
                'msg': 'Enable verbose output',
                'type': bool,
                'default': False
            }
        ])

        # VPIC simulation menu
        self.add_menu('vpic', msg="VPIC simulation commands")
        self.add_cmd('vpic run', keep_remainder=False, aliases=['vpic r'])
        self.add_args([
            {
                'name': 'steps',
                'msg': 'Number of simulation steps',
                'type': int,
                'required': True,
                'pos': True,
                'class': 'sim',
                'rank': 0
            },
            {
                'name': 'grid_size',
                'msg': 'Grid size',
                'type': int,
                'default': 256,
                'pos': True,
                'class': 'sim',
                'rank': 1
            },
            {
                'name': 'output_dir',
                'msg': 'Output directory',
                'type': str,
                'default': './output'
            },
            {
                'name': 'nodes',
                'msg': 'Compute nodes',
                'type': list,
                'aliases': ['n'],
                'args': [
                    {
                        'name': 'hostname',
                        'msg': 'Node hostname',
                        'type': str
                    },
                    {
                        'name': 'cores',
                        'msg': 'Number of cores',
                        'type': int
                    }
                ]
            }
        ])

    def main_menu(self):
        """Handler for main menu command"""
        print(f"Main menu called with: {self.kwargs}")
        print(f"Remainder: {self.remainder}")

    def vpic_run(self):
        """Handler for vpic run command"""
        print(f"Running VPIC simulation with {self.kwargs['steps']} steps")
        print(f"Grid size: {self.kwargs['grid_size']}")
        if 'nodes' in self.kwargs:
            print(f"Using nodes: {self.kwargs['nodes']}")

# Usage
parser = MyAppArgParse()
parser.define_options()

# Parse various command formats
result = parser.parse(['vpic', 'run', '1000', '512', '--output_dir=/tmp/sim'])
result = parser.parse(['vpic', 'r', '100'])  # Using alias
result = parser.parse(['--verbose=true', 'extra', 'args'])  # Main menu with remainder
```

## Command Handler Methods

When a command is parsed, the parser automatically calls a method named after the command:
- Command `"vpic run"` → calls `vpic_run()` method
- Command `""` (empty) → calls `main_menu()` method
- Spaces and hyphens in command names become underscores

## Error Handling

The parser raises `ValueError` for:
- Missing required arguments
- Invalid argument types during casting
- Attempting to add arguments without a command

## Advanced Features

### Argument Classes and Ranking
Use `'class'` and `'rank'` to control positional argument order:

```python
{
    'name': 'input_file',
    'pos': True,
    'class': 'files',
    'rank': 0
},
{
    'name': 'output_file', 
    'pos': True,
    'class': 'files',
    'rank': 1
},
{
    'name': 'verbose',
    'pos': True,
    'class': 'options',
    'rank': 0
}
```

Order: `files` arguments first (input_file, output_file), then `options` arguments (verbose).

### Complex List Arguments
For structured list data:

```python
{
    'name': 'servers',
    'type': list,
    'args': [
        {'name': 'hostname', 'type': str},
        {'name': 'port', 'type': int},
        {'name': 'ssl', 'type': bool}
    ]
}
```

Usage: `--servers="[(server1, 8080, true), (server2, 8443, false)]"`

## Testing

Comprehensive unit tests are available at `test/unit/test_argparse.py` covering:
- Command aliases
- Argument ranking and ordering
- List argument parsing (both set and append modes)
- Type casting
- Required argument validation
- Remainder handling
- Edge cases and error conditions

## Best Practices

1. **Define clear argument classes** for logical grouping of positional arguments
2. **Use meaningful rank values** to control argument order within classes
3. **Provide aliases** for frequently used commands and arguments
4. **Set appropriate defaults** for optional arguments
5. **Use descriptive names and messages** for better user experience
6. **Implement command handler methods** with matching names
7. **Test edge cases** thoroughly, especially with complex list arguments
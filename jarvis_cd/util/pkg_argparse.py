"""
PkgArgParse - Argument parser for package configuration

Supported types in configure_menu:
- str: String values
- int: Integer values
- float: Float values
- bool: Boolean values (supports 'true', '1', 'yes', 'on' for True; 'false', '0', 'no', 'off' for False)
- list: List of values
- dict: Dictionary values (supports Python dict literal syntax)
- SizeType: Size specifications (e.g., "1k", "2M", "10G")
- Custom types: Any type with a constructor that accepts string values
"""
from .argparse import ArgParse
from typing import List, Dict, Any


class PkgArgParse(ArgParse):
    """
    Argument parser specifically for package configuration.
    Provides a single 'configure' command with arguments from package's configure_menu().

    Supported argument types:
    - str: String values
    - int: Integer values
    - float: Float values
    - bool: Boolean values (use +arg/-arg or --arg true/false)
    - list: List of values (supports multiple --arg values or Python list syntax)
    - dict: Dictionary values (supports Python dict literal syntax)
    - SizeType: Size specifications like "1k", "2M", "10G" (binary multipliers)
    - Custom types: Any type with a constructor accepting strings
    """

    def __init__(self, pkg_name: str, configure_menu: List[Dict[str, Any]]):
        """
        Initialize package argument parser.

        :param pkg_name: Name of the package
        :param configure_menu: List of argument specifications from configure_menu()
        """
        super().__init__()

        self.pkg_name = pkg_name

        # Add the configure command
        self.add_cmd(
            'configure',
            msg=f'Configure {pkg_name} package',
            keep_remainder=False
        )

        # Add arguments from configure_menu
        if configure_menu:
            self.add_args(configure_menu)

    def print_help(self, cmd_name: str = None):
        """
        Print help for the package configuration.

        :param cmd_name: Command name (always 'configure' for packages)
        """
        if cmd_name and cmd_name != 'configure':
            print(f"Unknown command: {cmd_name}")
            print("Only 'configure' command is available for packages")
            return

        # Print package header
        print(f"Package: {self.pkg_name}")
        print()
        print("Configuration Parameters:")
        print()

        # Print the configure command help
        self.print_command_help('configure')

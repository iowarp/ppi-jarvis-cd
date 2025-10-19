import re
import ast
from typing import Dict, List, Any, Optional


class ArgParse:
    def __init__(self):
        self.menus = {}
        self.commands = {}
        self.command_args = {}
        self.kwargs = {}
        self.remainder = []
        self.current_menu = None
        self.current_command = None
        
    def add_menu(self, name: str, msg: str = ""):
        """Add a menu to the parser"""
        self.menus[name] = {
            'name': name,
            'msg': msg,
            'commands': []
        }
        
    def add_cmd(self, name: str, msg: str = "", keep_remainder: bool = False, aliases: Optional[List[str]] = None):
        """Add a command to a menu"""
        if aliases is None:
            aliases = []
            
        # Extract menu name from command name
        parts = name.split()
        menu_name = ' '.join(parts[:-1]) if len(parts) > 1 else ''
        cmd_name = parts[-1] if parts else name
        
        self.commands[name] = {
            'name': name,
            'menu': menu_name,
            'cmd_name': cmd_name,
            'msg': msg,
            'keep_remainder': keep_remainder,
            'aliases': aliases,
            'args': []
        }
        
        # Add to menu's command list
        if menu_name in self.menus:
            self.menus[menu_name]['commands'].append(name)
            
        # Add aliases to commands dict
        for alias in aliases:
            self.commands[alias] = self.commands[name]
            
    def add_args(self, args_list: List[Dict[str, Any]]):
        """Add arguments to the most recently added command"""
        if not self.commands:
            raise ValueError("No command to add arguments to")
            
        # Get the last added command (excluding aliases)
        last_cmd = None
        for cmd_name, cmd_info in reversed(list(self.commands.items())):
            # Check if this is not an alias by seeing if it equals itself
            if cmd_name == cmd_info['name']:
                last_cmd = cmd_name
                break
                
        if last_cmd is None:
            last_cmd = list(self.commands.keys())[-1]
                
        self.command_args[last_cmd] = args_list
        
    def _parse_list_value(self, value: str, arg_spec: Dict[str, Any]) -> List[Any]:
        """Parse a list value from string representation"""
        try:
            # Remove surrounding quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
                
            # Handle Python-like list notation: "[item1, item2]" or "[(item1, item2), (item3, item4)]"
            if value.startswith('[') and value.endswith(']'):
                parsed = ast.literal_eval(value)
                return self._convert_list_items(parsed, arg_spec)
            else:
                # Handle single item that should be added to list
                return self._convert_list_items([self._parse_single_item(value, arg_spec)], arg_spec)
        except (ValueError, SyntaxError):
            # Fallback: try to parse as single item
            return [self._parse_single_item(value, arg_spec)]
            
    def _parse_single_item(self, value: str, arg_spec: Dict[str, Any]) -> Any:
        """Parse a single item for a list"""
        args_def = arg_spec.get('args', [])
        
        if not args_def:
            return value
        
        # Remove surrounding quotes if present
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
            
        # Handle tuple-like notation: "(item1, item2)"
        if value.startswith('(') and value.endswith(')'):
            try:
                parsed = ast.literal_eval(value)
                if isinstance(parsed, tuple):
                    result = {}
                    for i, arg_def in enumerate(args_def):
                        if i < len(parsed):
                            result[arg_def['name']] = self._cast_value(parsed[i], arg_def.get('type', str))
                    return result
            except (ValueError, SyntaxError):
                pass
                
        # Handle single value
        if len(args_def) == 1:
            return {args_def[0]['name']: self._cast_value(value, args_def[0].get('type', str))}
            
        return value
        
    def _convert_list_items(self, items: List[Any], arg_spec: Dict[str, Any]) -> List[Any]:
        """Convert list items according to the argument specification"""
        args_def = arg_spec.get('args', [])
        result = []

        for item in items:
            if isinstance(item, tuple) and args_def:
                # Convert tuple to dict based on args definition
                item_dict = {}
                for i, arg_def in enumerate(args_def):
                    if i < len(item):
                        item_dict[arg_def['name']] = self._cast_value(item[i], arg_def.get('type', str))
                result.append(item_dict)
            elif isinstance(item, dict) and args_def:
                # Convert dict values based on args definition
                item_dict = {}
                for arg_def in args_def:
                    arg_name = arg_def['name']
                    if arg_name in item:
                        item_dict[arg_name] = self._cast_value(item[arg_name], arg_def.get('type', str))
                    else:
                        # Keep other keys as-is
                        item_dict.update({k: v for k, v in item.items() if k not in [a['name'] for a in args_def]})
                result.append(item_dict)
            elif isinstance(item, dict):
                result.append(item)
            else:
                # Single value - if there's exactly one arg_def, convert it
                if args_def and len(args_def) == 1:
                    arg_def = args_def[0]
                    result.append(self._cast_value(item, arg_def.get('type', str)))
                else:
                    result.append(item)

        return result
        
    def _cast_value(self, value: Any, value_type: type, arg_spec: Dict[str, Any] = None) -> Any:
        """
        Cast a value to the specified type.

        Supported types: str, int, float, bool, list, dict, SizeType, and custom types.

        :param value: Value to cast
        :param value_type: Target type
        :param arg_spec: Full argument specification (optional, used for nested list/dict conversions)
        """
        if value_type == bool:
            if isinstance(value, bool):
                return value
            elif isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            else:
                return bool(value)
        elif value_type == int:
            return int(value)
        elif value_type == float:
            return float(value)
        elif value_type == str:
            return str(value)
        elif value_type == list:
            if isinstance(value, list):
                # If arg_spec provided with nested args, convert list items
                if arg_spec and 'args' in arg_spec:
                    return self._convert_list_items(value, arg_spec)
                return value
            return [value]
        elif value_type == dict:
            if isinstance(value, dict):
                # If arg_spec provided with nested args, convert dict values
                if arg_spec and 'args' in arg_spec:
                    converted = {}
                    args_def = arg_spec.get('args', [])
                    for arg_def in args_def:
                        arg_name = arg_def['name']
                        if arg_name in value:
                            converted[arg_name] = self._cast_value(value[arg_name], arg_def.get('type', str), arg_def)
                    # Keep other keys as-is
                    for k, v in value.items():
                        if k not in converted:
                            converted[k] = v
                    return converted
                return value
            # Try to parse as dict
            if isinstance(value, str):
                # Try Python literal syntax first (JSON-like format)
                if (value.startswith('{') and value.endswith('}')) or (value.startswith('[') and value.endswith(']')):
                    try:
                        import ast
                        result = ast.literal_eval(value)
                        # Apply type conversions if arg_spec has args
                        if isinstance(result, dict) and arg_spec and 'args' in arg_spec:
                            converted = {}
                            args_def = arg_spec.get('args', [])
                            for arg_def in args_def:
                                arg_name = arg_def['name']
                                if arg_name in result:
                                    converted[arg_name] = self._cast_value(result[arg_name], arg_def.get('type', str), arg_def)
                            # Keep other keys as-is
                            for k, v in result.items():
                                if k not in converted:
                                    converted[k] = v
                            return converted if converted else result
                        return result
                    except (ValueError, SyntaxError, TypeError):
                        pass

                # Try key:value,key2:value2 format (only if not JSON-like)
                if ':' in value and ',' in value and not value.startswith('{'):
                    try:
                        result = {}
                        pairs = value.split(',')
                        for pair in pairs:
                            if ':' in pair:
                                k, v = pair.split(':', 1)
                                k = k.strip()
                                v = v.strip()
                                # Apply type conversion if arg_spec has args
                                if arg_spec and 'args' in arg_spec:
                                    for arg_def in arg_spec['args']:
                                        if arg_def['name'] == k:
                                            v = self._cast_value(v, arg_def.get('type', str), arg_def)
                                            break
                                result[k] = v
                        if result:
                            return result
                    except Exception:
                        pass

                # Last resort: return as-is
                return value
            else:
                try:
                    return dict(value)
                except (ValueError, TypeError):
                    return value
        else:
            # For custom types (including SizeType), try direct conversion
            try:
                return value_type(value)
            except (ValueError, TypeError):
                return value
            
    def _find_command(self, args: List[str]) -> tuple[Optional[str], int]:
        """Find the best matching command and return it with the number of args consumed"""
        best_match = None
        best_length = 0
        
        for cmd_name in self.commands.keys():
            # Skip aliases, only check primary command names
            if cmd_name in self.commands and 'aliases' in self.commands[cmd_name] and cmd_name in self.commands[cmd_name]['aliases']:
                continue
                
            cmd_parts = cmd_name.split()
            if len(cmd_parts) <= len(args):
                if args[:len(cmd_parts)] == cmd_parts:
                    if len(cmd_parts) > best_length:
                        best_match = cmd_name
                        best_length = len(cmd_parts)
        
        # Check aliases
        for cmd_name, cmd_info in self.commands.items():
            if 'aliases' in cmd_info:
                for alias in cmd_info['aliases']:
                    alias_parts = alias.split()
                    if len(alias_parts) <= len(args):
                        if args[:len(alias_parts)] == alias_parts:
                            if len(alias_parts) > best_length:
                                best_match = cmd_name
                                best_length = len(alias_parts)
                        
        return best_match, best_length
        
    def _get_argument_info(self, cmd_name: str, arg_name: str) -> Optional[Dict[str, Any]]:
        """Get argument information for a command"""
        if cmd_name not in self.command_args:
            return None

        for arg_spec in self.command_args[cmd_name]:
            if arg_spec['name'] == arg_name:
                return arg_spec
            # Check aliases
            if 'aliases' in arg_spec and arg_name in arg_spec['aliases']:
                return arg_spec

        return None

    def _print_param_error(self, error_msg: str, cmd_name: str):
        """Print parameter error with usage menu and exit"""
        import sys
        print(f"Error: {error_msg}")
        print()
        self.print_command_help(cmd_name)
        sys.exit(1)
        
    def parse(self, args: List[str]) -> Dict[str, Any]:
        """Parse the argument list"""
        self.kwargs = {}
        self.remainder = []
        self.current_menu = None
        self.current_command = None

        # Check for help request
        if args and (args[0] in ['--help', '-h', 'help']):
            if len(args) > 1:
                # Help for specific command/menu
                self.print_help(' '.join(args[1:]))
            else:
                # General help
                self.print_help()
            return {}

        if not args:
            self.current_command = ''
            return self._handle_command('')

        # Find matching command
        cmd_name, consumed = self._find_command(args)

        if cmd_name is None:
            # Check for multi-word menus first (e.g., "ppl env")
            for i in range(min(3, len(args)), 0, -1):  # Check up to 3 words, longest first
                potential_menu = ' '.join(args[:i])
                if potential_menu in self.menus:
                    # Check if there's a help flag in the remaining args
                    remaining_args = args[i:]
                    if '--help' in remaining_args or '-h' in remaining_args:
                        self.print_menu_help(potential_menu)
                        return {}
                    # If no help flag, treat as menu navigation
                    self.print_menu_help(potential_menu)
                    return {}

            # Check if there's an empty command defined (default command)
            if '' in self.commands:
                cmd_name = ''
                consumed = 0
            elif self.commands or self.menus:
                # Unknown command - exit with error if there are menus or commands defined (but no default)
                import sys
                print(f"Error: Unknown command '{' '.join(args)}'")
                print()
                self.print_help()
                sys.exit(1)
            else:
                # Default to empty command (if nothing is defined)
                cmd_name = ''
                consumed = 0

        self.current_command = cmd_name
        remaining_args = args[consumed:]

        # Check for help in remaining args
        if '--help' in remaining_args or '-h' in remaining_args:
            self.print_command_help(cmd_name)
            return {}

        try:
            return self._parse_command_args(cmd_name, remaining_args)
        except ValueError as e:
            self._print_param_error(str(e), cmd_name)
        
    def _parse_command_args(self, cmd_name: str, args: List[str]) -> Dict[str, Any]:
        """Parse arguments for a specific command"""
        if cmd_name not in self.command_args:
            # If no args defined, treat all as remainder
            if cmd_name in self.commands and self.commands[cmd_name]['keep_remainder']:
                self.remainder = args
            return self._handle_command(cmd_name)

        arg_specs = self.command_args[cmd_name]
        keep_remainder = self.commands[cmd_name]['keep_remainder']

        # Initialize defaults
        for arg_spec in arg_specs:
            if 'default' in arg_spec:
                self.kwargs[arg_spec['name']] = arg_spec['default']

        # Separate positional and keyword args by class and rank
        positional_args = []
        for arg_spec in arg_specs:
            if arg_spec.get('pos', False):
                positional_args.append(arg_spec)

        # Sort positional args by class and rank
        # Arguments with a class should be sorted by (class, rank)
        # Arguments without a class should come after classed arguments
        def sort_key(x):
            class_name = x.get('class', '')
            rank = x.get('rank', 0)
            # If no class, put it at the end with a high sort value
            if not class_name:
                return ('zzz_no_class', rank)
            return (class_name, rank)

        positional_args.sort(key=sort_key)

        i = 0
        pos_index = 0

        while i < len(args):
            arg = args[i]

            # Handle key=value format (for any argument, not just --)
            # Only treat as key=value if key looks like a valid argument name (alphanumeric + underscore, no spaces)
            if '=' in arg and not arg.startswith('-'):
                key, value = arg.split('=', 1)
                # Check if key looks like an argument name (no spaces, alphanumeric/underscore)
                if key and not ' ' in key and key.replace('_', '').replace('-', '').isalnum():
                    # Remove surrounding quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    arg_spec = self._get_argument_info(cmd_name, key)
                    if arg_spec:
                        if arg_spec.get('type') == list:
                            self.kwargs[arg_spec['name']] = self._parse_list_value(value, arg_spec)
                        else:
                            self.kwargs[arg_spec['name']] = self._cast_value(value, arg_spec.get('type', str), arg_spec)
                        i += 1
                        continue
                    # If not a known arg, fall through to positional handling

            if arg.startswith('--'):
                # Long option
                if '=' in arg:
                    # --key=value format
                    key, value = arg[2:].split('=', 1)
                    arg_spec = self._get_argument_info(cmd_name, key)
                    if arg_spec:
                        if arg_spec.get('type') == list:
                            self.kwargs[arg_spec['name']] = self._parse_list_value(value, arg_spec)
                        else:
                            self.kwargs[arg_spec['name']] = self._cast_value(value, arg_spec.get('type', str), arg_spec)
                    else:
                        # Unknown argument
                        self._print_param_error(f"Unknown argument '{key}'", cmd_name)
                    i += 1
                else:
                    # --key value format
                    key = arg[2:]
                    arg_spec = self._get_argument_info(cmd_name, key)
                    if arg_spec:
                        if i + 1 < len(args):
                            value = args[i + 1]
                            if arg_spec.get('type') == list:
                                # Append mode for lists without =
                                if arg_spec['name'] not in self.kwargs:
                                    self.kwargs[arg_spec['name']] = []
                                elif not isinstance(self.kwargs[arg_spec['name']], list):
                                    self.kwargs[arg_spec['name']] = [self.kwargs[arg_spec['name']]]
                                parsed_item = self._parse_single_item(value, arg_spec)
                                self.kwargs[arg_spec['name']].append(parsed_item)
                            else:
                                self.kwargs[arg_spec['name']] = self._cast_value(value, arg_spec.get('type', str), arg_spec)
                            i += 2
                        else:
                            # Missing value for argument
                            self._print_param_error(f"Argument '{key}' requires a value", cmd_name)
                    else:
                        # Unknown argument
                        self._print_param_error(f"Unknown argument '{key}'", cmd_name)
            elif arg.startswith('+') and len(arg) > 1:
                # +arg format for boolean true
                key = arg[1:]
                arg_spec = self._get_argument_info(cmd_name, key)
                if arg_spec and arg_spec.get('type') == bool:
                    self.kwargs[arg_spec['name']] = True
                    i += 1
                    continue
                else:
                    # If not a boolean arg, treat as positional
                    if pos_index < len(positional_args):
                        arg_spec = positional_args[pos_index]
                        self.kwargs[arg_spec['name']] = self._cast_value(arg, arg_spec.get('type', str), arg_spec)
                        pos_index += 1
                        i += 1
                    else:
                        # Remainder
                        if keep_remainder:
                            self.remainder.extend(args[i:])
                            break
                        i += 1
            elif arg.startswith('-') and len(arg) > 1 and not arg[1:].isdigit():
                # Check for -arg format for boolean false first
                key = arg[1:]
                arg_spec = self._get_argument_info(cmd_name, key)
                if arg_spec and arg_spec.get('type') == bool:
                    self.kwargs[arg_spec['name']] = False
                    i += 1
                    continue

                # Short option with value
                if arg_spec and i + 1 < len(args):
                    value = args[i + 1]
                    if arg_spec.get('type') == list:
                        # Append mode for lists
                        if arg_spec['name'] not in self.kwargs:
                            self.kwargs[arg_spec['name']] = []
                        elif not isinstance(self.kwargs[arg_spec['name']], list):
                            self.kwargs[arg_spec['name']] = [self.kwargs[arg_spec['name']]]
                        parsed_item = self._parse_single_item(value, arg_spec)
                        self.kwargs[arg_spec['name']].append(parsed_item)
                    else:
                        self.kwargs[arg_spec['name']] = self._cast_value(value, arg_spec.get('type', str), arg_spec)
                    i += 2
                else:
                    i += 1
            else:
                # Positional argument
                if pos_index < len(positional_args):
                    arg_spec = positional_args[pos_index]
                    self.kwargs[arg_spec['name']] = self._cast_value(arg, arg_spec.get('type', str), arg_spec)
                    pos_index += 1
                    i += 1
                else:
                    # Remainder
                    if keep_remainder:
                        self.remainder.extend(args[i:])
                        break
                    i += 1

        # Check required args
        for arg_spec in arg_specs:
            if arg_spec.get('required', False) and arg_spec['name'] not in self.kwargs:
                self._print_param_error(f"Required argument '{arg_spec['name']}' not provided", cmd_name)

        # Validate choices
        for arg_spec in arg_specs:
            if 'choices' in arg_spec and arg_spec['choices'] and arg_spec['name'] in self.kwargs:
                value = self.kwargs[arg_spec['name']]
                if value not in arg_spec['choices']:
                    self._print_param_error(f"Argument '{arg_spec['name']}' must be one of {arg_spec['choices']}, got: {value}", cmd_name)

        return self._handle_command(cmd_name)
        
    def _handle_command(self, cmd_name: str) -> Dict[str, Any]:
        """Handle command execution"""
        # Call the appropriate method if it exists
        method_name = cmd_name.replace(' ', '_').replace('-', '_') or 'main_menu'
        if hasattr(self, method_name):
            getattr(self, method_name)()
        return self.kwargs
        
    def print_help(self, target: str = ""):
        """Print help information"""
        if target:
            # Help for specific command or menu
            if target in self.commands:
                self.print_command_help(target)
            elif target in self.menus:
                self.print_menu_help(target)
            else:
                print(f"No help available for '{target}'")
        else:
            # General help - show all top-level menus and commands
            self.print_general_help()
            
    def print_general_help(self):
        """Print general help showing all available menus and commands"""
        print("Usage: [command] [options]")
        print()

        # Show top-level menus and their commands
        top_level_menus = [name for name, menu in self.menus.items() if name and ' ' not in name]
        if top_level_menus:
            print("Available menus:")
            for menu_name in sorted(top_level_menus):
                menu = self.menus[menu_name]
                msg = menu.get('msg', '')
                print(f"  {menu_name:<15} {msg}")

                # Show commands under this menu
                if menu['commands']:
                    for cmd_name in menu['commands']:
                        if cmd_name in self.commands:
                            cmd = self.commands[cmd_name]
                            # Show command with indentation
                            display_name = cmd['cmd_name']
                            cmd_msg = cmd.get('msg', '')
                            print(f"    {display_name:<13} {cmd_msg}")
            print()

        # Show top-level commands (commands with no menu or empty menu)
        top_level_commands = [name for name, cmd in self.commands.items()
                            if cmd['menu'] == '' and name == cmd['name']]  # Exclude aliases
        if top_level_commands:
            print("Available commands:")
            for cmd_name in sorted(top_level_commands):
                cmd = self.commands[cmd_name]
                msg = cmd.get('msg', '')
                aliases_str = f" (aliases: {', '.join(cmd['aliases'])})" if cmd['aliases'] else ""
                print(f"  {cmd_name:<15} {msg}{aliases_str}")
            print()

        print("Use 'help [menu|command]' or '[menu|command] --help' for more information")
        
    def print_menu_help(self, menu_name: str):
        """Print help for a specific menu"""
        if menu_name not in self.menus:
            print(f"Menu '{menu_name}' not found")
            return
            
        menu = self.menus[menu_name]
        print(f"Menu: {menu_name}")
        if menu.get('msg'):
            print(f"Description: {menu['msg']}")
        print()
        
        if menu['commands']:
            print("Available commands:")
            for cmd_name in menu['commands']:
                if cmd_name in self.commands:
                    cmd = self.commands[cmd_name]
                    # Extract just the command part (after the menu name)
                    display_name = cmd['cmd_name']
                    msg = cmd.get('msg', '')
                    aliases_str = f" (aliases: {', '.join(cmd['aliases'])})" if cmd['aliases'] else ""
                    print(f"  {display_name:<15} {msg}{aliases_str}")
        else:
            print("No commands available in this menu")
            
    def print_command_help(self, cmd_name: str):
        """Print help for a specific command"""
        if cmd_name not in self.commands:
            print(f"Command '{cmd_name}' not found")
            return
            
        cmd = self.commands[cmd_name]
        print(f"Command: {cmd_name}")
        if cmd.get('msg'):
            print(f"Description: {cmd['msg']}")
        
        if cmd['aliases']:
            print(f"Aliases: {', '.join(cmd['aliases'])}")
        print()
        
        # Show arguments if any
        if cmd_name in self.command_args:
            args = self.command_args[cmd_name]
            if args:
                print("Arguments:")
                
                # Separate positional and optional arguments
                positional = [arg for arg in args if arg.get('pos', False)]
                optional = [arg for arg in args if not arg.get('pos', False)]
                
                if positional:
                    print("  Positional arguments:")
                    for arg in sorted(positional, key=lambda x: (x.get('class', ''), x.get('rank', 0))):
                        self._print_argument_help(arg, "    ")
                        
                if optional:
                    print("  Optional arguments:")
                    for arg in optional:
                        self._print_argument_help(arg, "    ")
        else:
            print("No arguments defined for this command")
            
    def _print_argument_help(self, arg: Dict[str, Any], indent: str = ""):
        """Print help for a single argument"""
        name = arg['name']
        msg = arg.get('msg', 'No description')
        arg_type = arg.get('type', str).__name__
        default = arg.get('default')
        required = arg.get('required', False)
        choices = arg.get('choices')
        aliases = arg.get('aliases', [])
        
        # Build argument display
        if arg.get('pos', False):
            arg_display = f"{name}"
        else:
            arg_display = f"--{name}"
            if aliases:
                alias_display = ', '.join([f"-{a}" if len(a) == 1 else f"--{a}" for a in aliases])
                arg_display += f", {alias_display}"
            
            # Add +/- syntax for boolean arguments
            if arg.get('type') == bool:
                arg_display += f", +{name}, -{name}"
                
        print(f"{indent}{arg_display}")
        print(f"{indent}  {msg}")
        
        details = []
        if required:
            details.append("required")
        if default is not None:
            details.append(f"default: {default}")
        if choices:
            details.append(f"choices: {choices}")
        details.append(f"type: {arg_type}")
        
        if details:
            print(f"{indent}  ({', '.join(details)})")

    def parse_dict(self, cmd_name: str, arg_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse arguments from a dictionary with type conversion.

        :param cmd_name: Command name to parse for
        :param arg_dict: Dictionary of argument name -> value
        :return: Parsed arguments with proper types
        """
        self.kwargs = {}
        self.remainder = []  # No remainder support for dict parsing
        self.current_menu = None
        self.current_command = cmd_name

        # Check if command exists
        if cmd_name not in self.commands:
            raise ValueError(f"Command '{cmd_name}' not found")

        try:
            # Get argument specifications for this command
            if cmd_name not in self.command_args:
                # No arguments defined, just return the dict as-is with casting
                self.kwargs = arg_dict.copy()
                return self._handle_command(cmd_name)

            arg_specs = self.command_args[cmd_name]

            # Initialize defaults
            for arg_spec in arg_specs:
                if 'default' in arg_spec:
                    self.kwargs[arg_spec['name']] = arg_spec['default']

            # Process each argument from the dictionary
            for arg_name, arg_value in arg_dict.items():
                # Find the argument specification
                arg_spec = self._get_argument_info(cmd_name, arg_name)

                if arg_spec is None:
                    # Unknown argument - still include it but without type conversion
                    self.kwargs[arg_name] = arg_value
                    continue

                # Convert value to proper type
                if arg_spec.get('type') == list:
                    # Handle list arguments
                    if isinstance(arg_value, list):
                        self.kwargs[arg_spec['name']] = self._convert_list_items(arg_value, arg_spec)
                    else:
                        # Single value for list - wrap in list
                        self.kwargs[arg_spec['name']] = [self._parse_single_item(str(arg_value), arg_spec)]
                else:
                    # Handle scalar arguments
                    self.kwargs[arg_spec['name']] = self._cast_value(arg_value, arg_spec.get('type', str), arg_spec)

            # Check required arguments
            for arg_spec in arg_specs:
                if arg_spec.get('required', False) and arg_spec['name'] not in self.kwargs:
                    self._print_param_error(f"Required argument '{arg_spec['name']}' not provided", cmd_name)

            # Validate choices
            for arg_spec in arg_specs:
                if 'choices' in arg_spec and arg_spec['choices'] and arg_spec['name'] in self.kwargs:
                    value = self.kwargs[arg_spec['name']]
                    if value not in arg_spec['choices']:
                        self._print_param_error(f"Argument '{arg_spec['name']}' must be one of {arg_spec['choices']}, got: {value}", cmd_name)

            return self._handle_command(cmd_name)
        except (ValueError, TypeError) as e:
            self._print_param_error(f"Error converting argument: {e}", cmd_name)

    def define_options(self):
        """Override this method to define your command structure"""
        pass
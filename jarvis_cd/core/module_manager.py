"""
Module management system for Jarvis-CD.
Provides functionality for creating and managing modulefiles for manually-installed packages.
"""
import os
import yaml
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from jarvis_cd.core.config import Jarvis
from jarvis_cd.util.logger import logger
from jarvis_cd.shell.exec_factory import Exec
from jarvis_cd.shell.exec_info import LocalExecInfo


class ModuleManager:
    """
    Manages modulefiles for manually-installed packages.
    Provides creation, configuration, and generation of TCL and YAML modulefiles.
    """

    def __init__(self, jarvis_config: Jarvis):
        """
        Initialize module manager.

        :param jarvis_config: Jarvis configuration singleton
        """
        self.jarvis_config = jarvis_config
        self.jarvis = jarvis_config  # They are the same now
        
        # Module directory structure
        self.modules_root = Path.home() / '.ppi-jarvis-mods'
        self.packages_dir = self.modules_root / 'packages'
        self.modules_dir = self.modules_root / 'modules'
        
        # Ensure directories exist
        self.packages_dir.mkdir(parents=True, exist_ok=True)
        self.modules_dir.mkdir(parents=True, exist_ok=True)
        
    def create_module(self, mod_name: str):
        """
        Create a new module with directory structure and files.
        
        :param mod_name: Name of the module to create
        """
        # Create package directory
        package_dir = self.packages_dir / mod_name
        package_dir.mkdir(exist_ok=True)
        
        # Create src subdirectory
        src_dir = package_dir / 'src'
        src_dir.mkdir(exist_ok=True)
        
        # Create initial YAML file with default paths
        yaml_file = self.modules_dir / f'{mod_name}.yaml'
        
        # Get the package root directory path
        package_root = str(package_dir)
        
        initial_yaml = {
            'deps': {},
            'doc': {
                'Name': mod_name,
                'Version': 'None',
                'doc': 'None'
            },
            'prepends': {
                'CFLAGS': [],
                'CMAKE_PREFIX_PATH': [
                    f'{package_root}/cmake'
                ],
                'CPATH': [],
                'INCLUDE': [],
                'LDFLAGS': [],
                'LD_LIBRARY_PATH': [
                    f'{package_root}/lib',
                    f'{package_root}/lib64'
                ],
                'LIBRARY_PATH': [
                    f'{package_root}/lib',
                    f'{package_root}/lib64'
                ],
                'PATH': [
                    f'{package_root}/bin',
                    f'{package_root}/sbin'
                ],
                'PKG_CONFIG_PATH': [
                    f'{package_root}/lib/pkgconfig',
                    f'{package_root}/lib64/pkgconfig'
                ],
                'PYTHONPATH': [
                    f'{package_root}/bin',
                    f'{package_root}/lib',
                    f'{package_root}/lib64'
                ]
            },
            'setenvs': {}
        }
        
        with open(yaml_file, 'w') as f:
            yaml.dump(initial_yaml, f, default_flow_style=False)
        
        # Generate initial TCL file
        self._generate_tcl_file(mod_name)
        
        # Set as current module
        self.jarvis_config.set_current_module(mod_name)
        
        print(f"Created module: {mod_name}")
        print(f"Package directory: {package_dir}")
        print(f"YAML file: {yaml_file}")
        print(f"TCL file: {self.modules_dir / mod_name}")
        
    def set_current_module(self, mod_name: str):
        """
        Set the current module in jarvis config.
        
        :param mod_name: Name of the module to set as current
        """
        if not self._module_exists(mod_name):
            raise ValueError(f"Module '{mod_name}' does not exist")
            
        self.jarvis_config.set_current_module(mod_name)
        print(f"Set current module: {mod_name}")
        
    def prepend_env_vars(self, mod_name: Optional[str], env_args: List[str]):
        """
        Prepend environment variables to module configuration.
        
        :param mod_name: Module name (optional, uses current if None)
        :param env_args: Environment arguments in ENV=VAL1;VAL2;VAL3 format
        """
        # Check if mod_name looks like an environment argument (contains =)
        if mod_name and '=' in mod_name:
            # First argument is actually an env var, prepend it to env_args
            env_args = [mod_name] + env_args
            mod_name = None
            
        if mod_name is None:
            mod_name = self.jarvis_config.get_current_module()
            if not mod_name:
                raise ValueError("No current module set. Use 'jarvis mod cd <module>' or specify module name")
        
        if not self._module_exists(mod_name):
            raise ValueError(f"Module '{mod_name}' does not exist")
        
        # Load current YAML configuration
        yaml_file = self.modules_dir / f'{mod_name}.yaml'
        with open(yaml_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Parse environment arguments
        for arg in env_args:
            if '=' not in arg:
                print(f"Warning: Ignoring malformed argument: {arg}")
                continue
                
            env_var, values_str = arg.split('=', 1)
            values = [v.strip() for v in values_str.split(';') if v.strip()]
            
            # Ensure prepends section exists
            if 'prepends' not in config:
                config['prepends'] = {}
            
            # Initialize environment variable list if not exists
            if env_var not in config['prepends']:
                config['prepends'][env_var] = []
            
            # Prepend new values (reverse order to maintain precedence)
            for value in reversed(values):
                if value not in config['prepends'][env_var]:
                    config['prepends'][env_var].insert(0, value)
        
        # Save updated configuration
        with open(yaml_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        # Regenerate TCL file
        self._generate_tcl_file(mod_name)
        
        print(f"Updated prepend environment variables for module: {mod_name}")
        
    def set_env_vars(self, mod_name: Optional[str], env_args: List[str]):
        """
        Set environment variables in module configuration.
        
        :param mod_name: Module name (optional, uses current if None)
        :param env_args: Environment arguments in ENV=VAL format
        """
        # Check if mod_name looks like an environment argument (contains =)
        if mod_name and '=' in mod_name:
            # First argument is actually an env var, prepend it to env_args
            env_args = [mod_name] + env_args
            mod_name = None
            
        if mod_name is None:
            mod_name = self.jarvis_config.get_current_module()
            if not mod_name:
                raise ValueError("No current module set. Use 'jarvis mod cd <module>' or specify module name")
        
        if not self._module_exists(mod_name):
            raise ValueError(f"Module '{mod_name}' does not exist")
        
        # Load current YAML configuration
        yaml_file = self.modules_dir / f'{mod_name}.yaml'
        with open(yaml_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Parse environment arguments
        for arg in env_args:
            if '=' not in arg:
                print(f"Warning: Ignoring malformed argument: {arg}")
                continue
                
            env_var, value = arg.split('=', 1)
            
            # Ensure setenvs section exists
            if 'setenvs' not in config:
                config['setenvs'] = {}
            
            # Set environment variable
            config['setenvs'][env_var] = value
        
        # Save updated configuration
        with open(yaml_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        # Regenerate TCL file
        self._generate_tcl_file(mod_name)
        
        print(f"Updated set environment variables for module: {mod_name}")
        
    def destroy_module(self, mod_name: Optional[str]):
        """
        Destroy a module by removing its directory and configuration files.
        
        :param mod_name: Module name (optional, uses current if None)
        """
        if mod_name is None:
            mod_name = self.jarvis_config.get_current_module()
            if not mod_name:
                raise ValueError("No current module set. Use 'jarvis mod cd <module>' or specify module name")
        
        if not self._module_exists(mod_name):
            raise ValueError(f"Module '{mod_name}' does not exist")
        
        # Remove package directory
        package_dir = self.packages_dir / mod_name
        if package_dir.exists():
            shutil.rmtree(package_dir)
        
        # Remove module files
        yaml_file = self.modules_dir / f'{mod_name}.yaml'
        tcl_file = self.modules_dir / mod_name
        
        if yaml_file.exists():
            yaml_file.unlink()
        if tcl_file.exists():
            tcl_file.unlink()
        
        # Clear current module if it was the destroyed one
        current_module = self.jarvis_config.get_current_module()
        if current_module == mod_name:
            self.jarvis_config.set_current_module(None)

        print(f"Destroyed module: {mod_name}")

    def clear_module(self, mod_name: Optional[str]):
        """
        Clear module directory contents except for the src/ directory.
        Useful for cleaning up build artifacts while preserving source code.

        :param mod_name: Module name (optional, uses current if None)
        """
        if mod_name is None:
            mod_name = self.jarvis_config.get_current_module()
            if not mod_name:
                raise ValueError("No current module set. Use 'jarvis mod cd <module>' or specify module name")

        if not self._module_exists(mod_name):
            raise ValueError(f"Module '{mod_name}' does not exist")

        # Get package directory
        package_dir = self.packages_dir / mod_name
        if not package_dir.exists():
            logger.warning(f"Package directory does not exist: {package_dir}")
            return

        # Get src directory
        src_dir = package_dir / 'src'

        # Remove all contents except src/
        items_removed = 0
        for item in package_dir.iterdir():
            if item.name == 'src':
                continue  # Skip src directory

            try:
                if item.is_dir():
                    shutil.rmtree(item)
                    logger.info(f"Removed directory: {item.name}/")
                else:
                    item.unlink()
                    logger.info(f"Removed file: {item.name}")
                items_removed += 1
            except Exception as e:
                logger.error(f"Failed to remove {item.name}: {e}")

        if items_removed > 0:
            logger.success(f"Cleared module '{mod_name}': removed {items_removed} items (preserved src/)")
        else:
            logger.info(f"Module '{mod_name}' is already clean (only src/ exists)")

    def get_module_src_dir(self, mod_name: Optional[str]) -> str:
        """
        Get the source directory path for a module.
        
        :param mod_name: Module name (optional, uses current if None)
        :return: Source directory path
        """
        if mod_name is None:
            mod_name = self.jarvis_config.get_current_module()
            if not mod_name:
                raise ValueError("No current module set. Use 'jarvis mod cd <module>' or specify module name")
        
        if not self._module_exists(mod_name):
            raise ValueError(f"Module '{mod_name}' does not exist")
        
        return str(self.packages_dir / mod_name / 'src')
        
    def get_module_root_dir(self, mod_name: Optional[str]) -> str:
        """
        Get the root directory path for a module.
        
        :param mod_name: Module name (optional, uses current if None)
        :return: Root directory path
        """
        if mod_name is None:
            mod_name = self.jarvis_config.get_current_module()
            if not mod_name:
                raise ValueError("No current module set. Use 'jarvis mod cd <module>' or specify module name")
        
        if not self._module_exists(mod_name):
            raise ValueError(f"Module '{mod_name}' does not exist")
        
        return str(self.packages_dir / mod_name)
        
    def get_module_tcl_path(self, mod_name: Optional[str]) -> str:
        """
        Get the TCL file path for a module.
        
        :param mod_name: Module name (optional, uses current if None)
        :return: TCL file path
        """
        if mod_name is None:
            mod_name = self.jarvis_config.get_current_module()
            if not mod_name:
                raise ValueError("No current module set. Use 'jarvis mod cd <module>' or specify module name")
        
        return str(self.modules_dir / mod_name)
        
    def get_module_yaml_path(self, mod_name: Optional[str]) -> str:
        """
        Get the YAML file path for a module.
        
        :param mod_name: Module name (optional, uses current if None)
        :return: YAML file path
        """
        if mod_name is None:
            mod_name = self.jarvis_config.get_current_module()
            if not mod_name:
                raise ValueError("No current module set. Use 'jarvis mod cd <module>' or specify module name")
        
        return str(self.modules_dir / f'{mod_name}.yaml')
        
    def build_profile(self, path: Optional[str] = None, method: str = 'dotenv'):
        """
        Create a snapshot of important currently-loaded environment variables.
        
        :param path: Output file path (if None, print to stdout)
        :param method: Output format (dotenv, cmake, clion, vscode)
        :return: Environment profile dictionary
        """
        env_vars = ['PATH', 'LD_LIBRARY_PATH', 'LIBRARY_PATH',
                    'INCLUDE', 'CPATH', 'PKG_CONFIG_PATH', 'CMAKE_PREFIX_PATH',
                    'JAVA_HOME', 'PYTHONPATH']
        
        profile = {}
        for env_var in env_vars:
            env_data = self._get_env(env_var)
            if len(env_data) == 0:
                profile[env_var] = []
            else:
                profile[env_var] = env_data.split(':')
        
        self._output_profile(profile, path, method)
        return profile
        
    def build_profile_new(self, path=None, method=None):
        """
        Create a snapshot of important currently-loaded environment variables.

        :param path: Output file path (optional)
        :param method: Output format (dotenv, cmake, clion, vscode)
        :return: Environment profile dictionary
        """
        env_vars = ['PATH', 'LD_LIBRARY_PATH', 'LIBRARY_PATH',
                    'INCLUDE', 'CPATH', 'PKG_CONFIG_PATH', 'CMAKE_PREFIX_PATH',
                    'JAVA_HOME', 'PYTHONPATH']
        profile = {}
        for env_var in env_vars:
            env_data = self._get_env(env_var)
            if len(env_data) == 0:
                profile[env_var] = []
            else:
                profile[env_var] = env_data.split(':')
        self.env_profile(profile, path, method)
        return profile

    def env_profile(self, profile, path=None, method='dotenv'):
        """Output environment profile in specified format."""
        # None-path profiles (print to stdout)
        if method == 'clion':
            prof_list = [f'{env_var}={":".join(env_data)}'
                        for env_var, env_data in profile.items()]
            print(';'.join(prof_list))
        elif method == 'vscode':
            vars_list = [f'  "{env_var}": "{":".join(env_data)}"' for env_var, env_data in profile.items()]
            print('"environment": {')
            print(',\n'.join(vars_list))
            print('}')
        elif method == 'dotenv' and path is None:
            # Print dotenv format to stdout if no path specified
            for env_var, env_data in profile.items():
                print(f'{env_var}="{":".join(env_data)}"')
        
        if path is None:
            return
        
        # Path-based profiles
        with open(path, 'w') as f:
            if method == 'dotenv':
                for env_var, env_data in profile.items():
                    f.write(f'{env_var}="{":".join(env_data)}"\n')
            elif method == 'cmake':
                for env_var, env_data in profile.items():
                    f.write(f'set(ENV{{{env_var}}} "{":".join(env_data)}")\n')

    def import_module(self, mod_name: str, command: str):
        """
        Create a module by detecting environment changes before/after running a command.
        
        :param mod_name: Name of the module to create
        :param command: Command to execute and analyze
        """
        print(f"Importing module '{mod_name}' from command: {command}")
        
        # Environment variables to track
        env_vars_to_track = ['PATH', 'LD_LIBRARY_PATH', 'LIBRARY_PATH',
                            'INCLUDE', 'CPATH', 'PKG_CONFIG_PATH', 'CMAKE_PREFIX_PATH',
                            'JAVA_HOME', 'PYTHONPATH', 'CFLAGS', 'LDFLAGS']
        
        # Capture environment before command execution
        env_before = {}
        for env_var in env_vars_to_track:
            env_before[env_var] = os.environ.get(env_var, '')
        
        # Execute the command in a shell that will preserve the environment changes
        # We need to source the command and then print the environment
        shell_script = f"""#!/bin/bash
# Source the original environment
{command}
# Print environment variables we care about
echo "=== ENV_START ==="
"""
        
        for env_var in env_vars_to_track:
            shell_script += f'echo "{env_var}=${{{env_var}}}"\n'
        
        shell_script += 'echo "=== ENV_END ==="'
        
        # Execute the shell script with interactive shell to preserve functions
        exec_info = LocalExecInfo(collect_output=True)
        shell = os.environ.get('SHELL', '/bin/bash')
        executor = Exec(f'{shell} -i -c \'{shell_script}\'', exec_info)
        executor.run()
        
        # Check exit code (it's a dict with hostname keys)
        exit_code = executor.exit_code.get('localhost', 0) if isinstance(executor.exit_code, dict) else executor.exit_code
        if exit_code != 0:
            print(f"Warning: Command exited with non-zero code {exit_code}")
            if executor.stderr:
                stderr_text = ""
                if isinstance(executor.stderr, dict):
                    stderr_text = executor.stderr.get('localhost', '') or ""
                else:
                    stderr_text = executor.stderr or ""
                print(f"STDERR: {stderr_text}")
        
        # Handle different stdout formats (string or dict)
        stdout_text = ""
        if isinstance(executor.stdout, dict):
            stdout_text = executor.stdout.get('localhost', '') or ""
        else:
            stdout_text = executor.stdout or ""
        
        # Parse the environment variables from between the markers
        env_after = {}
        for env_var in env_vars_to_track:
            env_after[env_var] = ''
        
        lines = stdout_text.split('\n')
        in_env_section = False
        
        for line in lines:
            line = line.strip()
            if line == "=== ENV_START ===":
                in_env_section = True
                continue
            elif line == "=== ENV_END ===":
                in_env_section = False
                continue
            elif in_env_section and '=' in line:
                try:
                    var_name, var_value = line.split('=', 1)
                    if var_name in env_vars_to_track:
                        env_after[var_name] = var_value
                except ValueError:
                    continue
        
        # Calculate differences
        env_changes = {}
        for env_var in env_vars_to_track:
            before = env_before[env_var]
            after = env_after[env_var]
            
            if before != after:
                # Split paths and find new additions
                before_paths = set(before.split(':') if before else [])
                after_paths = after.split(':') if after else []
                
                # Remove empty strings
                before_paths.discard('')
                after_paths = [p for p in after_paths if p]
                
                # Find new paths that were added
                new_paths = []
                for path in after_paths:
                    if path not in before_paths:
                        new_paths.append(path)
                
                if new_paths:
                    env_changes[env_var] = new_paths
        
        if not env_changes:
            print("No environment changes detected - creating empty module")
        else:
            print(f"Detected {len(env_changes)} environment variable changes")
        
        # Create the module
        self.create_module(mod_name)
        
        # Update the module configuration with detected changes
        yaml_file = self.modules_dir / f'{mod_name}.yaml'
        with open(yaml_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Add the command to the config
        config['command'] = command
        
        # Update prepends with detected changes
        for env_var, new_paths in env_changes.items():
            if 'prepends' not in config:
                config['prepends'] = {}
            if env_var not in config['prepends']:
                config['prepends'][env_var] = []
            
            # Prepend the new paths (reverse order to maintain precedence)
            for path in reversed(new_paths):
                if path not in config['prepends'][env_var]:
                    config['prepends'][env_var].insert(0, path)
        
        # Save the updated configuration
        with open(yaml_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        # Regenerate the TCL file
        self._generate_tcl_file(mod_name)
        
        print(f"Module '{mod_name}' imported successfully")
        
    def update_module(self, mod_name: Optional[str] = None):
        """
        Update a module by re-running its stored command.
        
        :param mod_name: Module name (optional, uses current if None)
        """
        if mod_name is None:
            mod_name = self.jarvis_config.get_current_module()
            if not mod_name:
                raise ValueError("No current module set. Use 'jarvis mod cd <module>' or specify module name")
        
        if not self._module_exists(mod_name):
            raise ValueError(f"Module '{mod_name}' does not exist")
        
        # Load the module configuration to get the stored command
        yaml_file = self.modules_dir / f'{mod_name}.yaml'
        with open(yaml_file, 'r') as f:
            config = yaml.safe_load(f)
        
        stored_command = config.get('command')
        if not stored_command:
            raise ValueError(f"Module '{mod_name}' has no stored command - cannot update")
        
        print(f"Updating module '{mod_name}' with stored command: {stored_command}")
        
        # Remove the existing module (except the package directory)
        yaml_file = self.modules_dir / f'{mod_name}.yaml'
        tcl_file = self.modules_dir / mod_name
        
        if tcl_file.exists():
            tcl_file.unlink()
        
        # Re-import the module with the stored command
        self.import_module(mod_name, stored_command)
        
    def list_modules(self):
        """List all available modules."""
        if not self.modules_dir.exists():
            print("No modules found")
            return
            
        yaml_files = list(self.modules_dir.glob('*.yaml'))
        if not yaml_files:
            print("No modules found")
            return
        
        current_module = self.jarvis_config.get_current_module()
        
        print("Available modules:")
        for yaml_file in sorted(yaml_files):
            mod_name = yaml_file.stem
            marker = " *" if mod_name == current_module else "  "
            print(f"{marker} {mod_name}")

    def add_dependency(self, mod_name: Optional[str], dep_name: str):
        """
        Add a module dependency.

        :param mod_name: Module name (None for current module)
        :param dep_name: Dependency module name to add
        """
        # Use current module if not specified
        if mod_name is None:
            mod_name = self.jarvis_config.get_current_module()
            if not mod_name:
                logger.error("No current module set. Please specify a module name or use 'jarvis mod cd <mod_name>' first.")
                return

        # Check if module exists
        if not self._module_exists(mod_name):
            logger.error(f"Module '{mod_name}' does not exist")
            return

        # Load YAML configuration
        yaml_file = self.modules_dir / f'{mod_name}.yaml'
        with open(yaml_file, 'r') as f:
            config = yaml.safe_load(f)

        # Ensure deps section exists
        if 'deps' not in config:
            config['deps'] = {}

        # Add dependency
        config['deps'][dep_name] = True

        # Save updated configuration
        with open(yaml_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        # Regenerate TCL file
        self._generate_tcl_file(mod_name)

        logger.success(f"Added dependency '{dep_name}' to module '{mod_name}'")

    def remove_dependency(self, mod_name: Optional[str], dep_name: str):
        """
        Remove a module dependency.

        :param mod_name: Module name (None for current module)
        :param dep_name: Dependency module name to remove
        """
        # Use current module if not specified
        if mod_name is None:
            mod_name = self.jarvis_config.get_current_module()
            if not mod_name:
                logger.error("No current module set. Please specify a module name or use 'jarvis mod cd <mod_name>' first.")
                return

        # Check if module exists
        if not self._module_exists(mod_name):
            logger.error(f"Module '{mod_name}' does not exist")
            return

        # Load YAML configuration
        yaml_file = self.modules_dir / f'{mod_name}.yaml'
        with open(yaml_file, 'r') as f:
            config = yaml.safe_load(f)

        # Check if dependency exists
        if 'deps' not in config or dep_name not in config['deps']:
            logger.warning(f"Dependency '{dep_name}' not found in module '{mod_name}'")
            return

        # Remove dependency
        del config['deps'][dep_name]

        # Save updated configuration
        with open(yaml_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        # Regenerate TCL file
        self._generate_tcl_file(mod_name)

        logger.success(f"Removed dependency '{dep_name}' from module '{mod_name}'")

    def _module_exists(self, mod_name: str) -> bool:
        """Check if a module exists."""
        yaml_file = self.modules_dir / f'{mod_name}.yaml'
        return yaml_file.exists()
        
    def _generate_tcl_file(self, mod_name: str):
        """Generate TCL modulefile from YAML configuration."""
        yaml_file = self.modules_dir / f'{mod_name}.yaml'
        tcl_file = self.modules_dir / mod_name
        
        # Load YAML configuration
        with open(yaml_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Generate TCL content
        tcl_content = ['#%Module1.0']
        
        # Add documentation
        doc = config.get('doc', {})
        if 'Name' in doc:
            tcl_content.append(f"module-whatis 'Name: {doc['Name']}'")
        if 'Version' in doc:
            tcl_content.append(f"module-whatis 'Version: {doc['Version']}'")
        if 'doc' in doc:
            tcl_content.append(f"module-whatis 'doc: {doc['doc']}'")
        
        # Add dependencies
        deps = config.get('deps', {})
        for dep_name, enabled in deps.items():
            if enabled:
                tcl_content.append(f"module load {dep_name}")
        
        # Add prepend paths
        prepends = config.get('prepends', {})
        for env_var, paths in prepends.items():
            for path in paths:
                tcl_content.append(f"prepend-path {env_var} {path}")
        
        # Add set environment variables
        setenvs = config.get('setenvs', {})
        for env_var, value in setenvs.items():
            tcl_content.append(f"setenv {env_var} {value}")
        
        # Write TCL file
        with open(tcl_file, 'w') as f:
            f.write('\n'.join(tcl_content) + '\n')
            
    def _get_env(self, env_var: str) -> str:
        """Get environment variable value."""
        return os.environ.get(env_var, '')
        
    def _output_profile(self, profile: Dict[str, List[str]], path: Optional[str], method: str):
        """Output environment profile in specified format."""
        if method == 'clion':
            # CLion format - semicolon separated list
            prof_list = [f'{env_var}={":".join(env_data)}'
                        for env_var, env_data in profile.items()]
            print(';'.join(prof_list))
        elif method == 'vscode':
            # VSCode format - JSON environment block
            vars_list = [f'  "{env_var}": "{":".join(env_data)}"' 
                        for env_var, env_data in profile.items()]
            print('"environment": {')
            print(',\n'.join(vars_list))
            print('}')
        
        if path is None:
            return
        
        # Path-based profiles
        with open(path, 'w') as f:
            if method == 'dotenv':
                # .env format
                for env_var, env_data in profile.items():
                    f.write(f'{env_var}="{":".join(env_data)}"\n')
            elif method == 'cmake':
                # CMake format
                for env_var, env_data in profile.items():
                    f.write(f'set(ENV{{{env_var}}} "{":".join(env_data)}")\n')
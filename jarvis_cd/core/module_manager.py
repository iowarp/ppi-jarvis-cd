"""
Module management system for Jarvis-CD.
Provides functionality for creating and managing modulefiles for manually-installed packages.
"""
import os
import yaml
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from jarvis_cd.core.config import JarvisConfig, Jarvis
from jarvis_cd.util.logger import logger


class ModuleManager:
    """
    Manages modulefiles for manually-installed packages.
    Provides creation, configuration, and generation of TCL and YAML modulefiles.
    """
    
    def __init__(self, jarvis_config: JarvisConfig):
        """
        Initialize module manager.
        
        :param jarvis_config: Jarvis configuration manager
        """
        self.jarvis_config = jarvis_config
        self.jarvis = Jarvis.get_instance()
        
        # Module directory structure
        self.modules_root = Path.home() / '.jarvis-mods'
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
        
        # Create initial YAML file
        yaml_file = self.modules_dir / f'{mod_name}.yaml'
        initial_yaml = {
            'deps': {},
            'doc': {
                'Name': mod_name,
                'Version': 'None',
                'doc': 'None'
            },
            'prepends': {
                'CFLAGS': [],
                'CMAKE_PREFIX_PATH': [],
                'CPATH': [],
                'INCLUDE': [],
                'LDFLAGS': [],
                'LD_LIBRARY_PATH': [],
                'LIBRARY_PATH': [],
                'PATH': [],
                'PKG_CONFIG_PATH': [],
                'PYTHONPATH': []
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
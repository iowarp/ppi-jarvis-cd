"""
Base package classes for Jarvis-CD.
Provides the consolidated Pkg class and its subclasses for Services, Applications, and Interceptors.
"""

import os
import yaml
import time
import inspect
from pathlib import Path
from typing import Dict, Any, List, Optional
from jarvis_cd.core.config import Jarvis, load_class


class Pkg:
    """
    Consolidated base class for all Jarvis packages.
    Provides common functionality and interface for services, applications, and interceptors.
    """
    
    @classmethod
    def load_standalone(cls, package_spec: str):
        """
        Load a package instance for standalone operations (not in a pipeline context).
        
        :param package_spec: Package specification (repo.pkg or just pkg)
        :return: Package instance
        """
        from jarvis_cd.core.config import load_class, Jarvis
        
        jarvis = Jarvis.get_instance()
        
        # Parse package specification
        if '.' in package_spec:
            # Full specification like "builtin.ior"
            import_parts = package_spec.split('.')
            repo_name = import_parts[0]
            pkg_name = import_parts[1]
        else:
            # Just package name, search in repos
            full_spec = jarvis.jarvis_config.find_package(package_spec)
            if not full_spec:
                raise ValueError(f"Package not found: {package_spec}")
            import_parts = full_spec.split('.')
            repo_name = import_parts[0]
            pkg_name = import_parts[1]
            
        # Determine class name (convert snake_case to PascalCase)
        class_name = ''.join(word.capitalize() for word in pkg_name.split('_'))
        
        # Load class
        if repo_name == 'builtin':
            repo_path = str(jarvis.jarvis_config.get_builtin_repo_path())
        else:
            # Find repo path in registered repos
            repo_path = None
            for registered_repo in jarvis.jarvis_config.repos['repos']:
                if Path(registered_repo).name == repo_name:
                    repo_path = registered_repo
                    break
                    
            if not repo_path:
                raise ValueError(f"Repository not found: {repo_name}")
                
        import_str = f"{repo_name}.{pkg_name}.pkg"
        try:
            pkg_class = load_class(import_str, repo_path, class_name)
        except Exception as e:
            raise ValueError(f"Failed to load package '{package_spec}': Error loading class {class_name} from {import_str}: {e}")
        
        if not pkg_class:
            raise ValueError(f"Package class not found: {class_name} in {import_str}")
            
        # Create instance
        pkg_instance = pkg_class()
        
        # Set basic attributes for standalone use
        pkg_instance.pkg_id = pkg_name
        pkg_instance.global_id = f"standalone.{pkg_name}"
        
        return pkg_instance
    
    def __init__(self, pipeline=None):
        """
        Initialize package with default values.
        
        :param pipeline: Parent pipeline instance (optional for standalone packages)
        """
        self.jarvis = Jarvis.get_instance()
        self.pipeline = pipeline
        self.pkg_dir = None          # Directory containing the package source (pkg.py file)
        self.config_dir = None       # Directory for saving package configuration files
        self.shared_dir = None
        self.private_dir = None
        self.env = {}                # Base environment (everything except LD_PRELOAD)
        self.mod_env = {}           # Modified environment (exact replica of env + LD_PRELOAD)
        self.config = {'interceptors': {}}
        self.global_id = None
        self.pkg_id = None
        
        # Call user-defined initialization
        self._init()
        
        # Set pkg_dir to the directory containing this package's source
        self._detect_pkg_dir()
        
    def _init(self):
        """
        Override this method to initialize package-specific variables.
        Don't assume that self.config is initialized.
        This provides an overview of the parameters of this class.
        Default values should almost always be None.
        """
        pass
        
    def _configure_menu(self) -> List[Dict[str, Any]]:
        """
        Override this method to define configuration options.
        
        :return: List of configuration option dictionaries
        """
        return []
        
    def _configure(self, **kwargs):
        """
        Override this method to handle package configuration.
        Takes as input a dictionary with keys determined from _configure_menu.
        Updates self.config and generates application-specific configuration files.
        
        :param kwargs: Configuration parameters
        """
        self.update_config(kwargs, rebuild=False)
        
    def configure_menu(self):
        """
        Get the complete configuration menu including common parameters.
        Returns the menu in argument dictionary format so parameters can be set from command line.
        
        :return: List of configuration option dictionaries
        """
        # Get package-specific menu
        package_menu = self._configure_menu()
        
        # Add common parameters that all packages should have
        common_menu = [
            {
                'name': 'interceptors',
                'msg': 'List of interceptor package names to apply',
                'type': list,
                'default': [],
                'args': [
                    {
                        'name': 'interceptor_name',
                        'msg': 'Name of an interceptor package',
                        'type': str,
                    }
                ]
            },
            {
                'name': 'sleep',
                'msg': 'Sleep time in seconds',
                'type': int,
                'default': 0,
            },
            {
                'name': 'do_dbg',
                'msg': 'Enable debug mode',
                'type': bool,
                'default': False,
            },
            {
                'name': 'dbg_port',
                'msg': 'Debug port number',
                'type': int,
                'default': 1234,
            },
            {
                'name': 'log_level',
                'msg': 'Logging level',
                'type': str,
                'choices': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                'default': 'INFO',
            },
            {
                'name': 'timeout',
                'msg': 'Operation timeout in seconds',
                'type': int,
                'default': 300,
            },
            {
                'name': 'retry_count',
                'msg': 'Number of retry attempts',
                'type': int,
                'default': 3,
            },
            {
                'name': 'hide_output',
                'msg': 'Hide command output',
                'type': bool,
                'default': False,
            }
        ]
        
        # Combine package-specific and common menus
        return package_menu + common_menu
        
    def configure(self, **kwargs):
        """
        Public configuration method that calls internal _configure.
        
        :param kwargs: Configuration parameters
        :return: Configuration dictionary
        """
        # Ensure package directories are set
        self._ensure_directories()
        
        # Apply menu defaults first
        self._apply_menu_defaults()
        
        # Update configuration with provided parameters
        self.update_config(kwargs, rebuild=False)
        
        # Call the internal configuration method
        self._configure(**kwargs)
        
        return self.config.copy()
        
    def _ensure_directories(self):
        """
        Ensure package directories are set. Use pkg_id if available, otherwise use class name.
        Gets directory paths from the parent pipeline if available, otherwise uses global directories.
        """
        if not self.config_dir or not self.shared_dir or not self.private_dir:
            try:
                pkg_id = getattr(self, 'pkg_id', None) or self.__class__.__name__.lower()
                
                if self.pipeline and hasattr(self.pipeline, 'name'):
                    # Pipeline package - get directories from pipeline
                    pipeline_dir = self.jarvis.jarvis_config.get_pipeline_dir(self.pipeline.name)
                    if not self.config_dir:
                        self.config_dir = str(pipeline_dir / 'packages' / pkg_id / 'config')
                    if not self.shared_dir:
                        self.shared_dir = str(pipeline_dir / 'packages' / pkg_id / 'shared')
                    if not self.private_dir:
                        self.private_dir = str(pipeline_dir / 'packages' / pkg_id / 'private')
                else:
                    # Standalone package - use global directories
                    if not self.config_dir:
                        self.config_dir = str(Path(self.jarvis.config_dir) / 'packages' / pkg_id)
                    if not self.shared_dir:
                        self.shared_dir = str(Path(self.jarvis.shared_dir) / pkg_id)
                    if not self.private_dir:
                        self.private_dir = str(Path(self.jarvis.private_dir) / pkg_id)
                    
                # Create directories if they don't exist
                for dir_path in [self.config_dir, self.shared_dir, self.private_dir]:
                    if dir_path:
                        Path(dir_path).mkdir(parents=True, exist_ok=True)
                        
            except Exception as e:
                self.log(f"Warning: Could not set package directories: {e}")
                # Set fallback directories
                import tempfile
                temp_dir = tempfile.mkdtemp(prefix=f'jarvis_{self.__class__.__name__.lower()}_')
                if not self.config_dir:
                    self.config_dir = temp_dir
                if not self.shared_dir:
                    self.shared_dir = temp_dir
                if not self.private_dir:
                    self.private_dir = temp_dir
                    
    def _detect_pkg_dir(self):
        """
        Detect the directory containing this package's source code (where pkg.py is located).
        """
        try:
            # Get the file path of the class definition
            class_file = inspect.getfile(self.__class__)
            # Get the directory containing the package file
            self.pkg_dir = str(Path(class_file).parent)
        except Exception as e:
            # Fallback: leave pkg_dir as None if detection fails
            pass
            
    def _apply_menu_defaults(self):
        """
        Apply default values from the configuration menu to ensure all parameters have values.
        """
        menu = self.configure_menu()
        for item in menu:
            param_name = item.get('name')
            default_value = item.get('default')
            if param_name and param_name not in self.config and default_value is not None:
                self.config[param_name] = default_value
        
    def update_config(self, new_config: Dict[str, Any], rebuild: bool = True):
        """
        Update package configuration.
        
        :param new_config: New configuration values
        :param rebuild: Whether to rebuild configuration files
        """
        self.config.update(new_config)
        
        if rebuild and hasattr(self, '_configure'):
            self._configure(**self.config)
            
    def start(self):
        """
        Start the package.
        Called during pipeline run and start operations.
        Override this method in package implementations.
        """
        pass
        
    def stop(self):
        """
        Stop the package.
        Called during pipeline stop operations.
        Override this method in package implementations.
        """
        pass
        
    def kill(self):
        """
        Kill the package.
        Called during pipeline kill operations.
        Override this method in package implementations.
        """
        pass
        
    def clean(self):
        """
        Clean package data.
        Called during pipeline clean operations.
        Destroys all data for the package.
        Override this method in package implementations.
        """
        pass
        
    def status(self) -> str:
        """
        Override this method to return package status.
        Called during pipeline status operations.
        
        :return: Status string
        """
        return "unknown"
        
    def track_env(self, env_track_dict: Dict[str, str]):
        """
        Track environment variables.
        
        :param env_track_dict: Dictionary of environment variables to track
        """
        # Add to env (but not LD_PRELOAD)
        for key, value in env_track_dict.items():
            if key != 'LD_PRELOAD':
                self.env[key] = value
        
        # mod_env is exact replica of env plus LD_PRELOAD
        self.mod_env = self.env.copy()
        if 'LD_PRELOAD' in env_track_dict:
            self.mod_env['LD_PRELOAD'] = env_track_dict['LD_PRELOAD']
        
    def prepend_env(self, env_name: str, val: str):
        """
        Prepend a value to an environment variable.
        
        :param env_name: Environment variable name
        :param val: Value to prepend
        """
        # For LD_PRELOAD, only update mod_env
        if env_name == 'LD_PRELOAD':
            current_val = self.mod_env.get(env_name, '')
            if current_val:
                self.mod_env[env_name] = f"{val}:{current_val}"
            else:
                self.mod_env[env_name] = val
        else:
            # For other variables, update env
            current_val = self.env.get(env_name, '')
            if current_val:
                self.env[env_name] = f"{val}:{current_val}"
            else:
                self.env[env_name] = val
            
            # Keep mod_env in sync (exact replica of env + LD_PRELOAD)
            self.mod_env[env_name] = self.env[env_name]
            
    def setenv(self, env_name: str, val: str):
        """
        Set an environment variable.
        
        :param env_name: Environment variable name
        :param val: Value to set
        """
        # For LD_PRELOAD, only update mod_env
        if env_name == 'LD_PRELOAD':
            self.mod_env[env_name] = val
        else:
            # For other variables, update env
            self.env[env_name] = val
            
            # Keep mod_env in sync (exact replica of env + LD_PRELOAD)
            self.mod_env[env_name] = val
        
    def find_library(self, library_name: str) -> Optional[str]:
        """
        Find a shared library by searching LD_LIBRARY_PATH and system paths.
        
        :param library_name: Name of the library to find
        :return: Path to library if found, None otherwise
        """
        import shutil
        
        # Generate possible library filenames
        lib_filenames = [
            f"lib{library_name}.so",     # Standard shared library
            f"{library_name}.so",        # Library name as-is with .so
            f"lib{library_name}.a",      # Static library
            library_name                 # Exact name as provided
        ]
        
        # Collect all library search paths in priority order
        search_paths = []
        
        # 1. Package-specific environment (mod_env takes precedence over env)
        mod_ld_path = self.mod_env.get('LD_LIBRARY_PATH')
        if mod_ld_path:
            search_paths.extend(mod_ld_path.split(':'))
        
        env_ld_path = self.env.get('LD_LIBRARY_PATH')
        if env_ld_path:
            search_paths.extend(env_ld_path.split(':'))
            
        # 2. System LD_LIBRARY_PATH
        system_ld_path = os.environ.get('LD_LIBRARY_PATH')
        if system_ld_path:
            search_paths.extend(system_ld_path.split(':'))
        
        # 3. Common system library directories
        search_paths.extend([
            "/usr/lib",
            "/usr/local/lib", 
            "/usr/lib64",
            "/usr/local/lib64",
            "/lib",
            "/lib64"
        ])
        
        # Search for the library in all paths
        for search_path in search_paths:
            if not search_path:  # Skip empty paths
                continue
                
            search_dir = Path(search_path)
            if not search_dir.exists():
                continue
                
            for lib_filename in lib_filenames:
                lib_path = search_dir / lib_filename
                print(lib_path)
                if lib_path.exists():
                    return str(lib_path)
        
        # Fallback: try using shutil.which for executable-style lookup
        for lib_filename in lib_filenames:
            lib_path = shutil.which(lib_filename)
            if lib_path:
                return lib_path
                
        return None
        
    def add_interceptor(self, pkg_name: str, interceptor_instance):
        """
        Add an interceptor package instance to this package's configuration.
        Interceptors are stored as a dictionary mapping pkg_name to constructed package instances.
        
        :param pkg_name: Name/identifier for the interceptor package
        :param interceptor_instance: Constructed interceptor package instance
        """
        if not isinstance(self.config.get('interceptors'), dict):
            self.config['interceptors'] = {}
            
        self.config['interceptors'][pkg_name] = interceptor_instance
        
    def get_interceptors(self) -> Dict[str, Any]:
        """
        Get all interceptors associated with this package.
        
        :return: Dictionary mapping interceptor names to instances
        """
        return self.config.get('interceptors', {})
        
    def remove_interceptor(self, pkg_name: str) -> bool:
        """
        Remove an interceptor from this package's configuration.
        
        :param pkg_name: Name/identifier of the interceptor to remove
        :return: True if interceptor was removed, False if not found
        """
        interceptors = self.config.get('interceptors', {})
        if pkg_name in interceptors:
            del interceptors[pkg_name]
            return True
        return False
        
    def log(self, message, color=None):
        """
        Log a message with package context and optional color.
        
        :param message: Message to log
        :param color: Color to use (from jarvis_cd.util.logger.Color enum), defaults to package color
        """
        from jarvis_cd.util.logger import logger, Color
        
        formatted_message = f"[{self.__class__.__name__}] {message}"
        
        if color is not None:
            logger.print(color, formatted_message)
        else:
            # Default to package color (light green for package operations)
            logger.package(formatted_message)
        
    def sleep(self, time_sec=None):
        """
        Sleep for a specified amount of time.
        
        :param time_sec: Time to sleep in seconds. If not provided, uses self.config['sleep']
        """
        if time_sec is None:
            time_sec = self.config.get('sleep', 0)
            
        self.log(f"Sleeping for {time_sec} seconds")
        if time_sec > 0:
            time.sleep(time_sec)
            
    def copy_template_file(self, source_path, dest_path, replacements=None):
        """
        Copy a template file from source to destination, replacing template constants.
        
        Template constants have the format ##CONSTANT_NAME## and are replaced with
        values from the replacements dictionary.
        
        :param source_path: Path to the source template file
        :param dest_path: Path where the processed file should be saved
        :param replacements: Dictionary of replacements {CONSTANT_NAME: value}
        
        Example:
            self.copy_template_file(f'{self.pkg_dir}/config/hermes.xml',
                                   self.adios2_xml_path,
                                   replacements={'PPN': 1})
        """
        try:
            if replacements is None:
                replacements = {}
                
            # Read the template file
            with open(source_path, 'r') as f:
                content = f.read()
            
            # Replace template constants
            for key, value in replacements.items():
                template_token = f"##{key}##"
                content = content.replace(template_token, str(value))
            
            # Ensure destination directory exists
            dest_dir = Path(dest_path).parent
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Write the processed content to destination
            with open(dest_path, 'w') as f:
                f.write(content)
                
            self.log(f"Copied template file {source_path} -> {dest_path} with {len(replacements)} replacements")
            
        except FileNotFoundError:
            self.log(f"Error: Template file not found: {source_path}")
            raise
        except Exception as e:
            self.log(f"Error copying template file {source_path} -> {dest_path}: {e}")
            raise
            
    def save(self):
        """
        Save package state including configuration and environment variables.
        Saves to config_dir with config.yaml, env.yaml, and mod_env.yaml files.
        """
        try:
            # Ensure package config directory exists
            if self.config_dir:
                Path(self.config_dir).mkdir(parents=True, exist_ok=True)
                
                # Save configuration
                config_path = Path(self.config_dir) / 'config.yaml'
                with open(config_path, 'w') as f:
                    yaml.dump(self.config, f, default_flow_style=False)
                self.log(f"Saved configuration to {config_path}")
                
                # Save environment variables (env should not contain LD_PRELOAD)
                env_path = Path(self.config_dir) / 'env.yaml'
                with open(env_path, 'w') as f:
                    yaml.dump(self.env, f, default_flow_style=False)
                self.log(f"Saved environment to {env_path}")
                
                # Save mod_env (exact replica of env + LD_PRELOAD)
                mod_env_path = Path(self.config_dir) / 'mod_env.yaml'
                with open(mod_env_path, 'w') as f:
                    yaml.dump(self.mod_env, f, default_flow_style=False)
                self.log(f"Saved mod_env to {mod_env_path}")
                
            else:
                self.log("Warning: No config_dir set, cannot save package state")
                
        except Exception as e:
            self.log(f"Error saving package state: {e}")
            
    def load(self):
        """
        Load package state from saved files in config_dir.
        Loads config.yaml, env.yaml, and mod_env.yaml if they exist.
        """
        try:
            if not self.config_dir or not Path(self.config_dir).exists():
                self.log("No saved package state found")
                return
                
            # Load configuration
            config_path = Path(self.config_dir) / 'config.yaml'
            if config_path.exists():
                with open(config_path, 'r') as f:
                    saved_config = yaml.safe_load(f)
                    if saved_config:
                        self.config.update(saved_config)
                        self.log(f"Loaded configuration from {config_path}")
                        
            # Load environment variables
            env_path = Path(self.config_dir) / 'env.yaml'
            if env_path.exists():
                with open(env_path, 'r') as f:
                    saved_env = yaml.safe_load(f)
                    if saved_env:
                        self.env.update(saved_env)
                        self.log(f"Loaded environment from {env_path}")
                        
            # Load mod_env
            mod_env_path = Path(self.config_dir) / 'mod_env.yaml'
            if mod_env_path.exists():
                with open(mod_env_path, 'r') as f:
                    saved_mod_env = yaml.safe_load(f)
                    if saved_mod_env:
                        self.mod_env.update(saved_mod_env)
                        self.log(f"Loaded mod_env from {mod_env_path}")
                        
        except Exception as e:
            self.log(f"Error loading package state: {e}")
        
    
    def show_readme(self):
        """
        Show README.md for this package.
        """
        if not self.pkg_dir:
            print("Package directory not set - cannot locate README")
            return
            
        readme_path = Path(self.pkg_dir) / 'README.md'
        
        if readme_path.exists():
            print(f"=== README for {self.__class__.__name__} ===")
            print(f"Location: {readme_path}")
            print()
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(content)
            except Exception as e:
                print(f"Error reading README: {e}")
        else:
            print(f"No README found for package {self.__class__.__name__}")
            print(f"Expected location: {readme_path}")
    
    def show_paths(self, path_flags: Dict[str, bool]):
        """
        Show directory paths based on flags.
        
        :param path_flags: Dictionary of path flags to show
        """
        try:
            # Ensure directories are set
            self._ensure_directories()
            
            paths_to_show = []
            
            # Check each flag and add corresponding paths
            if path_flags.get('conf'):
                if self.config_dir:
                    paths_to_show.append(f"{self.config_dir}/config.yaml")
                    
            if path_flags.get('env'):
                if self.config_dir:
                    paths_to_show.append(f"{self.config_dir}/env.yaml")
                    
            if path_flags.get('mod_env'):
                if self.config_dir:
                    paths_to_show.append(f"{self.config_dir}/mod_env.yaml")
                    
            if path_flags.get('conf_dir'):
                if self.config_dir:
                    paths_to_show.append(self.config_dir)
                    
            if path_flags.get('shared_dir'):
                if self.shared_dir:
                    paths_to_show.append(self.shared_dir)
                    
            if path_flags.get('priv_dir'):
                if self.private_dir:
                    paths_to_show.append(self.private_dir)
                    
            if path_flags.get('pkg_dir'):
                if self.pkg_dir:
                    paths_to_show.append(self.pkg_dir)
            
            # Print only the paths, one per line (for shell usage)
            for path in paths_to_show:
                if path:  # Only print non-None paths
                    print(path)
                    
        except Exception as e:
            print(f"Error getting package paths: {e}", file=sys.stderr)


class Service(Pkg):
    """
    Base class for long-running services.
    Services typically need to be manually stopped.
    """
    
    def __init__(self, pipeline=None):
        super().__init__(pipeline=pipeline)
        
    def _init(self):
        """
        Initialize service-specific variables.
        Override in subclasses.
        """
        pass


class Application(Pkg):
    """
    Base class for applications that run and complete automatically.
    Applications typically don't need manual stopping.
    """
    
    def __init__(self, pipeline=None):
        super().__init__(pipeline=pipeline)
        
    def _init(self):
        """
        Initialize application-specific variables.
        Override in subclasses.
        """
        pass


class Interceptor(Pkg):
    """
    Base class for interceptors that modify environment variables.
    Interceptors route system and library calls to new functions.
    """
    
    def __init__(self, pipeline=None):
        super().__init__(pipeline=pipeline)
        
    def _init(self):
        """
        Initialize interceptor-specific variables.
        Override in subclasses.
        """
        pass
        
    def modify_env(self):
        """
        Override this method to modify the environment for interception.
        This is the main method interceptors should implement.
        """
        pass
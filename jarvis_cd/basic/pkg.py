"""
Base package classes for Jarvis-CD.
Provides the foundation for Services, Applications, and Interceptors.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from jarvis_cd.core.config import Jarvis


class Pkg:
    """
    Base class for all Jarvis packages.
    Provides common functionality and interface for services, applications, and interceptors.
    """
    
    def __init__(self):
        """
        Initialize package with default values.
        These will be set by Jarvis when the package is loaded.
        """
        self.pkg_dir = None
        self.shared_dir = None
        self.private_dir = None
        self.env = {}
        self.mod_env = {}  # Will be initialized as a copy of env when needed
        self.config = {'interceptors': {}}
        self.global_id = None
        self.pkg_id = None
        self.jarvis = Jarvis.get_instance()
        
        # Call user-defined initialization
        self._init()
        
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
        # Call the internal configuration method
        self._configure(**kwargs)
        
        return self.config.copy()
        
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
        Override this method to start the package.
        Called during 'jarvis ppl run' and 'jarvis ppl start'.
        """
        pass
        
    def stop(self):
        """
        Override this method to stop the package.
        Called during 'jarvis ppl run' and 'jarvis ppl stop'.
        """
        pass
        
    def kill(self):
        """
        Override this method to forcibly kill the package.
        Called during 'jarvis ppl kill'.
        """
        pass
        
    def clean(self):
        """
        Override this method to clean package data.
        Called during 'jarvis ppl clean'.
        Destroys all data for the package.
        """
        pass
        
    def status(self) -> str:
        """
        Override this method to return package status.
        Called during 'jarvis ppl status'.
        
        :return: Status string
        """
        return "unknown"
        
    def track_env(self, env_track_dict: Dict[str, str]):
        """
        Track environment variables.
        
        :param env_track_dict: Dictionary of environment variables to track
        """
        self.env.update(env_track_dict)
        # Ensure mod_env is a proper copy of env, not a reference
        self.mod_env = self.env.copy()
        self.mod_env.update(env_track_dict)
        
    def prepend_env(self, env_name: str, val: str):
        """
        Prepend a value to an environment variable.
        
        :param env_name: Environment variable name
        :param val: Value to prepend
        """
        current_val = self.env.get(env_name, '')
        if current_val:
            self.env[env_name] = f"{val}:{current_val}"
        else:
            self.env[env_name] = val
            
        # Ensure mod_env is a copy, not a reference
        if not self.mod_env or self.mod_env is self.env:
            self.mod_env = self.env.copy()
            
        # Also update mod_env
        current_mod_val = self.mod_env.get(env_name, '')
        if current_mod_val:
            self.mod_env[env_name] = f"{val}:{current_mod_val}"
        else:
            self.mod_env[env_name] = val
            
    def setenv(self, env_name: str, val: str):
        """
        Set an environment variable.
        
        :param env_name: Environment variable name
        :param val: Value to set
        """
        self.env[env_name] = val
        # Ensure mod_env is a copy, not a reference
        if not self.mod_env or self.mod_env is self.env:
            self.mod_env = self.env.copy()
        self.mod_env[env_name] = val
        
    def find_library(self, library_name: str) -> Optional[str]:
        """
        Find a shared library in the system paths.
        
        :param library_name: Name of the library to find
        :return: Path to library if found, None otherwise
        """
        # Simple implementation - in a real system this would check LD_LIBRARY_PATH
        import shutil
        
        # Try to find with lib prefix and .so suffix
        lib_file = f"lib{library_name}.so"
        lib_path = shutil.which(lib_file)
        if lib_path:
            return lib_path
            
        # Try without modifications
        lib_path = shutil.which(library_name)
        if lib_path:
            return lib_path
            
        # Check common library directories
        common_lib_dirs = [
            "/usr/lib",
            "/usr/local/lib",
            "/usr/lib64",
            "/usr/local/lib64"
        ]
        
        for lib_dir in common_lib_dirs:
            full_path = os.path.join(lib_dir, lib_file)
            if os.path.exists(full_path):
                return full_path
                
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


class Service(Pkg):
    """
    Base class for long-running services.
    Services typically need to be manually stopped.
    """
    
    def __init__(self):
        super().__init__()
        
    def _init(self):
        """
        Initialize service-specific variables.
        Override in subclasses.
        """
        pass
        
    def status(self) -> str:
        """
        Return service status.
        Override in subclasses to provide actual status checking.
        
        :return: Status string (e.g., "running", "stopped", "error")
        """
        return "unknown"


class Application(Pkg):
    """
    Base class for applications that run and complete automatically.
    Applications typically don't need manual stopping.
    """
    
    def __init__(self):
        super().__init__()
        
    def _init(self):
        """
        Initialize application-specific variables.
        Override in subclasses.
        """
        pass
        
    def stop(self):
        """
        Stop application (usually not needed for apps).
        Override if your application needs special stop handling.
        """
        pass


class Interceptor(Pkg):
    """
    Base class for interceptors that modify environment variables.
    Interceptors route system and library calls to new functions.
    """
    
    def __init__(self):
        super().__init__()
        
    def _init(self):
        """
        Initialize interceptor-specific variables.
        Override in subclasses.
        """
        pass
        
    def _configure(self, **kwargs):
        """
        Configure interceptor.
        Interceptors typically only modify environment variables.
        
        :param kwargs: Configuration parameters
        """
        self.update_config(kwargs, rebuild=False)
        
    def modify_env(self):
        """
        Override this method to modify the environment for interception.
        This is the main method interceptors should implement.
        """
        pass
        
    def start(self):
        """
        Start interceptor (typically just calls modify_env).
        """
        self.modify_env()
        
    def stop(self):
        """
        Stop interceptor (usually not needed).
        """
        pass
        
    def status(self) -> str:
        """
        Return interceptor status.
        
        :return: Status string
        """
        return "active" if 'LD_PRELOAD' in self.mod_env else "inactive"
        
    def log(self, message):
        """
        Simple logging method for interceptors.
        
        :param message: Message to log
        """
        print(f"[{self.__class__.__name__}] {message}")


class SimplePackage(Pkg):
    """
    A simple package class that supports interceptors.
    Provides basic functionality for packages that need interceptor support.
    """
    
    def __init__(self):
        super().__init__()
        self.ppl = None  # Will be set by the pipeline when loading
        
    def _init(self):
        """
        Initialize SimplePackage-specific variables.
        Override in subclasses.
        """
        pass
        
    def _configure_menu(self):
        """
        Create a CLI menu for the configurator method.
        Includes the interceptors parameter.
        
        :return: List of configuration option dictionaries
        """
        return [
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
            }
        ]
        
    def _configure(self, **kwargs):
        """
        Configure SimplePackage with interceptor support.
        Interceptors will be processed later during start().
        
        :param kwargs: Configuration parameters
        """
        # Call parent configuration
        super()._configure(**kwargs)
        
    def start(self):
        """
        Start the package, processing interceptors first.
        Override this method in subclasses to implement actual start logic.
        """
        # Process interceptors before starting
        self._process_interceptors()
        
        # Call the actual start implementation
        self._start()
        
    def _start(self):
        """
        Override this method in subclasses to implement actual start logic.
        This is called after interceptors have been processed.
        """
        pass
        
    def _process_interceptors(self):
        """
        Process the interceptors list during package start.
        Loads interceptor packages and calls their modify_env() methods.
        Ensures mod_env is a copy of env for isolation.
        """
        # Ensure mod_env is a copy (not pointer) to env for isolation
        if not self.mod_env or self.mod_env is self.env:
            self.mod_env = self.env.copy()
        
        # Get interceptors list from config
        interceptors_list = self.config.get('interceptors', [])
        
        if not interceptors_list:
            return
            
        from jarvis_cd.core.config import load_class, Jarvis
        jarvis = Jarvis.get_instance()
        
        for interceptor_name in interceptors_list:
            try:
                # Load interceptor package dynamically
                interceptor_instance = self._load_interceptor_package(interceptor_name)
                if not interceptor_instance:
                    self.log(f"Warning: Could not load interceptor '{interceptor_name}'")
                    continue
                    
                # Verify it's an interceptor and has modify_env method
                if not hasattr(interceptor_instance, 'modify_env'):
                    self.log(f"Warning: Package '{interceptor_name}' does not have modify_env() method")
                    continue
                    
                # Call modify_env to update the environment
                self.log(f"Applying interceptor: {interceptor_name}")
                
                # Set the interceptor's environment to match ours
                if hasattr(interceptor_instance, 'env'):
                    interceptor_instance.env = self.env.copy()
                if hasattr(interceptor_instance, 'mod_env'):
                    interceptor_instance.mod_env = self.mod_env
                    
                # Call modify_env to update our environment
                interceptor_instance.modify_env()
                
                # Copy back any changes to our mod_env
                if hasattr(interceptor_instance, 'mod_env'):
                    self.mod_env.update(interceptor_instance.mod_env)
                
            except Exception as e:
                self.log(f"Error processing interceptor '{interceptor_name}': {e}")
                
    def _load_interceptor_package(self, interceptor_name: str):
        """
        Load an interceptor package by name.
        
        :param interceptor_name: Name of the interceptor package to load
        :return: Interceptor package instance or None if not found
        """
        try:
            from jarvis_cd.core.config import load_class, Jarvis
            jarvis = Jarvis.get_instance()
            
            # For now, assume builtin interceptors - can be extended later
            pkg_type = f"builtin.{interceptor_name}"
            
            # Parse package specification
            import_parts = pkg_type.split('.')
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
                    self.log(f"Repository not found for interceptor: {repo_name}")
                    return None
                    
            import_str = f"{repo_name}.{pkg_name}.pkg"
            pkg_class = load_class(import_str, repo_path, class_name)
            
            if not pkg_class:
                self.log(f"Interceptor class not found: {class_name} in {import_str}")
                return None
                
            # Create instance
            interceptor_instance = pkg_class()
            
            # Set basic attributes
            if hasattr(interceptor_instance, 'pkg_id'):
                interceptor_instance.pkg_id = interceptor_name
            if hasattr(interceptor_instance, 'jarvis'):
                interceptor_instance.jarvis = jarvis
                
            return interceptor_instance
            
        except Exception as e:
            self.log(f"Error loading interceptor '{interceptor_name}': {e}")
            return None
                
    def log(self, message):
        """
        Simple logging method. Override in subclasses for more sophisticated logging.
        
        :param message: Message to log
        """
        print(f"[{self.__class__.__name__}] {message}")


# Example IOR application implementation (matches the specification)
class Ior(Application):
    """
    IOR benchmark application implementation.
    This serves as an example of how to implement an Application.
    """
    
    def _init(self):
        """Initialize IOR-specific variables"""
        self.ior_path = None
        self.start_time = None
        
    def _configure_menu(self):
        """
        Create a CLI menu for the configurator method.
        
        :return: List(dict)
        """
        return [
            {
                'name': 'write',
                'msg': 'Perform a write workload',
                'type': bool,
                'default': True,
            },
            {
                'name': 'read',
                'msg': 'Perform a read workload',
                'type': bool,
                'default': False,
            },
            {
                'name': 'xfer',
                'msg': 'The size of data transfer',
                'type': str,
                'default': '1m',
            },
            {
                'name': 'block',
                'msg': 'Amount of data to generate per-process',
                'type': str,
                'default': '32m',
                'aliases': ['block_size']
            },
            {
                'name': 'api',
                'msg': 'The I/O api to use',
                'type': str,
                'choices': ['posix', 'mpiio', 'hdf5'],
                'default': 'posix',
            },
            {
                'name': 'fpp',
                'msg': 'Use file-per-process',
                'type': bool,
                'default': False,
            },
            {
                'name': 'reps',
                'msg': 'Number of times to repeat',
                'type': int,
                'default': 1,
            },
            {
                'name': 'nprocs',
                'msg': 'Number of processes',
                'type': int,
                'default': 1,
            },
            {
                'name': 'ppn',
                'msg': 'The number of processes per node',
                'type': int,
                'default': 16,
            },
            {
                'name': 'out',
                'msg': 'Path to the output file',
                'type': str,
                'default': '/tmp/ior.bin',
                'aliases': ['output']
            },
            {
                'name': 'log',
                'msg': 'Path to IOR output log',
                'type': str,
                'default': None,
            },
        ]

    def _configure(self, **kwargs):
        """
        Converts the Jarvis configuration to application-specific configuration.
        
        :param kwargs: Configuration parameters for this pkg.
        :return: None
        """
        self.update_config(kwargs, rebuild=False)
        self.config['api'] = self.config['api'].upper()

    def start(self):
        """
        Launch IOR application.
        
        :return: None
        """
        import time
        self.start_time = time.time()
        
        cmd = [
            'ior',
            '-k',
            f'-b {self.config["block"]}',
            f'-t {self.config["xfer"]}',
            f'-a {self.config["api"]}',
            f'-o {self.config["out"]}',
        ]
        
        out = os.path.expandvars(self.config['out'])
        if self.config['write']:
            cmd.append('-w')
        if self.config['read']:
            cmd.append('-r')
        if self.config['fpp']:
            cmd.append('-F')
        if self.config['reps'] > 1:
            cmd.append(f'-i {self.config["reps"]}')
            
        # Create output directory
        if '.' in os.path.basename(out):
            os.makedirs(str(Path(out).parent), exist_ok=True)
        else:
            os.makedirs(out, exist_ok=True)
            
        print(f"Running IOR: {' '.join(cmd)}")
        
        # In a real implementation, this would use MpiExecInfo to run IOR
        # For now, just simulate the execution
        print(f"IOR simulation completed with {self.config['nprocs']} processes")
        
        self.start_time = time.time() - self.start_time

    def stop(self):
        """Stop IOR (not typically needed)"""
        pass

    def clean(self):
        """
        Clean IOR output files.
        
        :return: None
        """
        import glob
        
        out_pattern = self.config['out'] + '*'
        for file_path in glob.glob(out_pattern):
            try:
                os.remove(file_path)
                print(f"Removed: {file_path}")
            except OSError as e:
                print(f"Error removing {file_path}: {e}")

    def _get_stat(self, stat_dict):
        """
        Get statistics from the application.

        :param stat_dict: A dictionary of statistics.
        :return: None
        """
        if self.start_time:
            stat_dict[f'{self.pkg_id}.runtime'] = self.start_time
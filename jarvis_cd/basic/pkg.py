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
        self.mod_env = {}
        self.config = {}
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
        
    def configure(self, **kwargs):
        """
        Override this method to handle package configuration.
        Takes as input a dictionary with keys determined from _configure_menu.
        Updates self.config and generates application-specific configuration files.
        
        :param kwargs: Configuration parameters
        """
        self.update_config(kwargs, rebuild=False)
        
    def update_config(self, new_config: Dict[str, Any], rebuild: bool = True):
        """
        Update package configuration.
        
        :param new_config: New configuration values
        :param rebuild: Whether to rebuild configuration files
        """
        self.config.update(new_config)
        
        if rebuild and hasattr(self, 'configure'):
            self.configure(**self.config)
            
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
        
    def configure(self, **kwargs):
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

    def configure(self, **kwargs):
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
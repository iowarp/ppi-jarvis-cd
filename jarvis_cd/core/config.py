import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from jarvis_cd.util.hostfile import Hostfile


class JarvisConfig:
    """
    Manages Jarvis configuration files and directories.
    Handles ~/.jarvis/jarvis_config.yaml, repos.yaml, and resource_graph.yaml
    """
    
    def __init__(self, jarvis_root: Optional[str] = None):
        """
        Initialize Jarvis configuration manager.
        
        :param jarvis_root: Override default ~/.jarvis directory
        """
        if jarvis_root is None:
            self.jarvis_root = Path.home() / '.jarvis'
        else:
            self.jarvis_root = Path(jarvis_root)
            
        self.config_file = self.jarvis_root / 'jarvis_config.yaml'
        self.repos_file = self.jarvis_root / 'repos.yaml'
        self.resource_graph_file = self.jarvis_root / 'resource_graph.yaml'
        
        self._config = None
        self._repos = None
        self._resource_graph = None
        self._hostfile = None
        
    def initialize(self, config_dir: str, private_dir: str, shared_dir: str):
        """
        Initialize Jarvis configuration directories and files.
        
        :param config_dir: Directory for jarvis metadata
        :param private_dir: Machine-local data directory  
        :param shared_dir: Shared data directory across all machines
        """
        # Create jarvis root directory
        self.jarvis_root.mkdir(parents=True, exist_ok=True)
        
        # Create required directories
        Path(config_dir).mkdir(parents=True, exist_ok=True)
        Path(private_dir).mkdir(parents=True, exist_ok=True)
        Path(shared_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize default configuration
        default_config = {
            'config_dir': str(Path(config_dir).absolute()),
            'private_dir': str(Path(private_dir).absolute()),
            'shared_dir': str(Path(shared_dir).absolute()),
            'current_pipeline': None,
            'hostfile': None
        }
        
        # Save configuration
        self.save_config(default_config)
        
        # Initialize empty repos configuration
        default_repos = {
            'repos': []
        }
        self.save_repos(default_repos)
        
        # Initialize empty resource graph
        default_resource_graph = {
            'storage': {},
            'network': {}
        }
        self.save_resource_graph(default_resource_graph)
        
        print(f"Jarvis initialized at {self.jarvis_root}")
        print(f"Config directory: {config_dir}")
        print(f"Private directory: {private_dir}")
        print(f"Shared directory: {shared_dir}")
        
    @property
    def config(self) -> Dict[str, Any]:
        """Get jarvis configuration, loading if necessary"""
        if self._config is None:
            self._config = self.load_config()
        return self._config
        
    @property
    def repos(self) -> Dict[str, Any]:
        """Get repos configuration, loading if necessary"""
        if self._repos is None:
            self._repos = self.load_repos()
        return self._repos
        
    @property
    def resource_graph(self) -> Dict[str, Any]:
        """Get resource graph, loading if necessary"""
        if self._resource_graph is None:
            self._resource_graph = self.load_resource_graph()
        return self._resource_graph
        
    @property
    def hostfile(self) -> Hostfile:
        """Get current hostfile"""
        if self._hostfile is None:
            hostfile_path = self.config.get('hostfile')
            if hostfile_path and os.path.exists(hostfile_path):
                self._hostfile = Hostfile(path=hostfile_path)
            else:
                # Default to localhost
                self._hostfile = Hostfile()
        return self._hostfile
        
    def load_config(self) -> Dict[str, Any]:
        """Load jarvis configuration from file"""
        if not self.config_file.exists():
            raise FileNotFoundError(f"Jarvis not initialized. Run 'jarvis init' first.")
            
        with open(self.config_file, 'r') as f:
            return yaml.safe_load(f) or {}
            
    def load_repos(self) -> Dict[str, Any]:
        """Load repos configuration from file"""
        if not self.repos_file.exists():
            return {'repos': []}
            
        with open(self.repos_file, 'r') as f:
            return yaml.safe_load(f) or {'repos': []}
            
    def load_resource_graph(self) -> Dict[str, Any]:
        """Load resource graph from file"""
        if not self.resource_graph_file.exists():
            return {'storage': {}, 'network': {}}
            
        with open(self.resource_graph_file, 'r') as f:
            return yaml.safe_load(f) or {'storage': {}, 'network': {}}
            
    def save_config(self, config: Dict[str, Any]):
        """Save jarvis configuration to file"""
        self.jarvis_root.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        self._config = config
        
    def save_repos(self, repos: Dict[str, Any]):
        """Save repos configuration to file"""
        self.jarvis_root.mkdir(parents=True, exist_ok=True)
        with open(self.repos_file, 'w') as f:
            yaml.dump(repos, f, default_flow_style=False)
        self._repos = repos
        
    def save_resource_graph(self, resource_graph: Dict[str, Any]):
        """Save resource graph to file"""
        self.jarvis_root.mkdir(parents=True, exist_ok=True)
        with open(self.resource_graph_file, 'w') as f:
            yaml.dump(resource_graph, f, default_flow_style=False)
        self._resource_graph = resource_graph
        
    def add_repo(self, repo_path: str):
        """Add a repository to the repos configuration"""
        repo_path = str(Path(repo_path).absolute())
        repos = self.repos.copy()
        
        if repo_path not in repos['repos']:
            repos['repos'].insert(0, repo_path)  # Add to front for priority
            self.save_repos(repos)
            print(f"Added repository: {repo_path}")
        else:
            print(f"Repository already exists: {repo_path}")
            
    def remove_repo(self, repo_path: str):
        """Remove a repository from the repos configuration"""
        repo_path = str(Path(repo_path).absolute())
        repos = self.repos.copy()
        
        if repo_path in repos['repos']:
            repos['repos'].remove(repo_path)
            self.save_repos(repos)
            print(f"Removed repository: {repo_path}")
        else:
            print(f"Repository not found: {repo_path}")
            
    def set_hostfile(self, hostfile_path: str):
        """Set the hostfile path in configuration"""
        hostfile_path = str(Path(hostfile_path).absolute())
        if not os.path.exists(hostfile_path):
            raise FileNotFoundError(f"Hostfile not found: {hostfile_path}")
            
        config = self.config.copy()
        config['hostfile'] = hostfile_path
        self.save_config(config)
        self._hostfile = None  # Reset cached hostfile
        print(f"Set hostfile: {hostfile_path}")
        
    def get_pipeline_dir(self, pipeline_name: str) -> Path:
        """Get the directory for a specific pipeline"""
        config_dir = Path(self.config['config_dir'])
        pipeline_dir = config_dir / 'pipelines' / pipeline_name
        return pipeline_dir
        
    def get_current_pipeline_dir(self) -> Optional[Path]:
        """Get the directory for the current pipeline"""
        current_pipeline = self.config.get('current_pipeline')
        if current_pipeline:
            return self.get_pipeline_dir(current_pipeline)
        return None
        
    def set_current_pipeline(self, pipeline_name: str):
        """Set the current active pipeline"""
        config = self.config.copy()
        config['current_pipeline'] = pipeline_name
        self.save_config(config)
        
    def get_builtin_repo_path(self) -> Path:
        """Get path to builtin repository"""
        # First check if builtin repo is installed to ~/.jarvis/builtin
        user_builtin = self.jarvis_root / 'builtin'
        if user_builtin.exists():
            return user_builtin
            
        # Fall back to builtin repo in the same directory as this file (development)
        dev_builtin = Path(__file__).parent.parent / 'builtin'
        if dev_builtin.exists():
            return dev_builtin
            
        # Fall back to installed package location
        try:
            import importlib.util
            import importlib.metadata
            
            # Look for builtin in installed package
            dist = importlib.metadata.distribution('jarvis_cd')
            if hasattr(dist, 'files') and dist.files:
                for file in dist.files:
                    if 'builtin' in str(file) and str(file).endswith('builtin/__init__.py'):
                        return Path(file).parent.parent
        except Exception:
            pass
            
        # Default fallback
        return user_builtin
        
    def find_package(self, pkg_name: str) -> Optional[str]:
        """
        Find a package in registered repositories.
        Returns the full import path if found.
        """
        # Check builtin repo first
        builtin_path = self.get_builtin_repo_path()
        if self._check_package_exists(builtin_path, 'builtin', pkg_name):
            return f'builtin.{pkg_name}'
            
        # Check registered repos
        for repo_path in self.repos['repos']:
            repo_name = Path(repo_path).name
            if self._check_package_exists(repo_path, repo_name, pkg_name):
                return f'{repo_name}.{pkg_name}'
                
        return None
        
    def _check_package_exists(self, repo_path: str, repo_name: str, pkg_name: str) -> bool:
        """Check if a package exists in a repository"""
        package_file = Path(repo_path) / repo_name / pkg_name / 'package.py'
        return package_file.exists()
        
    def is_initialized(self) -> bool:
        """Check if Jarvis has been initialized"""
        return self.config_file.exists()


def load_class(import_str: str, path: str, class_name: str):
    """
    Loads a class from a python file.

    :param import_str: A python import string. E.g., for "myrepo.dir1.pkg"
    :param path: The absolute path to the directory which contains the
    beginning of the import statement.
    :param class_name: The name of the class in the file
    :return: The class data type
    """
    import sys
    
    fullpath = os.path.join(path, import_str.replace('.', '/') + '.py')
    if not os.path.exists(fullpath):
        return None
    sys.path.insert(0, path)
    module = __import__(import_str, fromlist=[class_name])
    cls = getattr(module, class_name)
    sys.path.pop(0)
    return cls
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from jarvis_cd.util.hostfile import Hostfile


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
    
    # If the exact path doesn't exist, try replacing the last component
    if not os.path.exists(fullpath):
        # Handle legacy naming: if looking for "package.py", try "pkg.py"
        if import_str.endswith('.package'):
            legacy_import_str = import_str[:-8] + '.pkg'  # Replace .package with .pkg
            fullpath = os.path.join(path, legacy_import_str.replace('.', '/') + '.py')
            if os.path.exists(fullpath):
                import_str = legacy_import_str
            else:
                return None
        else:
            return None
    
    sys.path.insert(0, path)
    try:
        module = __import__(import_str, fromlist=[class_name])
        cls = getattr(module, class_name, None)
        if cls is None:
            raise AttributeError(f"Class '{class_name}' not found in module '{import_str}'")
        return cls
    except ImportError as e:
        # Re-raise ImportError with more context instead of silently returning None
        raise ImportError(f"Failed to import module '{import_str}' from path '{path}': {e}") from e
    except AttributeError as e:
        # Re-raise AttributeError with more context instead of silently returning None
        raise AttributeError(f"Failed to get class '{class_name}' from module '{import_str}': {e}") from e
    finally:
        sys.path.pop(0)


class Jarvis:
    """
    Singleton class that manages Jarvis configuration and provides global access.
    Combines configuration management with singleton pattern.
    """
    _instance = None

    def __new__(cls, jarvis_root: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, jarvis_root: Optional[str] = None):
        """Initialize singleton (only happens once)"""
        if self._initialized:
            return

        # Set up jarvis root directory
        if jarvis_root is None:
            self.jarvis_root = Path.home() / '.ppi-jarvis'
        else:
            self.jarvis_root = Path(jarvis_root)

        self.config_file = self.jarvis_root / 'jarvis_config.yaml'
        self.repos_file = self.jarvis_root / 'repos.yaml'
        self.resource_graph_file = self.jarvis_root / 'resource_graph.yaml'

        # Lazy-loaded properties
        self._config = None
        self._repos = None
        self._resource_graph = None
        self._hostfile = None

        # Directory paths
        self.config_dir = None
        self.private_dir = None
        self.shared_dir = None

        # Try to automatically load configuration if it exists
        if self.is_initialized():
            config = self.config
            self.config_dir = config.get('config_dir', str(self.jarvis_root))
            self.private_dir = config.get('private_dir', str(self.jarvis_root / 'private'))
            self.shared_dir = config.get('shared_dir', str(self.jarvis_root / 'shared'))

        self._initialized = True

    @classmethod
    def get_instance(cls, jarvis_root: Optional[str] = None):
        """Get the singleton instance"""
        if cls._instance is None:
            cls._instance = cls(jarvis_root)
        return cls._instance

    def initialize(self, config_dir: str, private_dir: str, shared_dir: str, force: bool = False):
        """
        Initialize Jarvis configuration directories and files.

        :param config_dir: Directory for jarvis metadata
        :param private_dir: Machine-local data directory
        :param shared_dir: Shared data directory across all machines
        :param force: Force override of existing repos and resource_graph files
        """
        from jarvis_cd.util import logger

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

        # Update instance attributes
        self.config_dir = default_config['config_dir']
        self.private_dir = default_config['private_dir']
        self.shared_dir = default_config['shared_dir']

        # Handle repos.yaml
        repos_exists = self.repos_file.exists()
        if repos_exists and not force:
            logger.warning(f"Existing repos.yaml detected - preserving (use +force to override)")
        elif repos_exists and force:
            logger.warning(f"Existing repos.yaml detected - overriding due to +force")
            builtin_repo_path = self.get_builtin_repo_path()
            if builtin_repo_path.exists():
                builtin_repo_path_str = str(builtin_repo_path.absolute())
            else:
                builtin_repo_path_str = str((self.jarvis_root / 'builtin').absolute())
            default_repos = {'repos': [builtin_repo_path_str]}
            self.save_repos(default_repos)
        else:
            # File doesn't exist, create it
            builtin_repo_path = self.get_builtin_repo_path()
            if builtin_repo_path.exists():
                builtin_repo_path_str = str(builtin_repo_path.absolute())
            else:
                builtin_repo_path_str = str((self.jarvis_root / 'builtin').absolute())
            default_repos = {'repos': [builtin_repo_path_str]}
            self.save_repos(default_repos)

        # Handle resource_graph.yaml
        resource_graph_exists = self.resource_graph_file.exists()
        if resource_graph_exists and not force:
            logger.warning(f"Existing resource_graph.yaml detected - preserving (use +force to override)")
        elif resource_graph_exists and force:
            logger.warning(f"Existing resource_graph.yaml detected - overriding due to +force")
            default_resource_graph = {'storage': {}, 'network': {}}
            self.save_resource_graph(default_resource_graph)
        else:
            # File doesn't exist, create it
            default_resource_graph = {'storage': {}, 'network': {}}
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

    def add_repo(self, repo_path: str, force: bool = False):
        """Add a repository to the repos configuration"""
        repo_path = str(Path(repo_path).absolute())
        repos = self.repos.copy()

        # Check for existing repository with same name (not just same path)
        repo_name = Path(repo_path).name
        existing_repos_with_same_name = [
            existing_path for existing_path in repos['repos']
            if Path(existing_path).name == repo_name
        ]

        if repo_path in repos['repos']:
            if force:
                # Repository path already exists - remove and re-add to update order
                repos['repos'].remove(repo_path)
                repos['repos'].insert(0, repo_path)
                self.save_repos(repos)
                print(f"Repository already exists - updated position: {repo_path}")
            else:
                print(f"Repository already exists: {repo_path}")
                print("Use --force to override existing repository")
        elif existing_repos_with_same_name:
            if force:
                # Remove existing repositories with same name
                for existing_path in existing_repos_with_same_name:
                    repos['repos'].remove(existing_path)
                    print(f"Removed existing repository: {existing_path}")
                # Add new repository
                repos['repos'].insert(0, repo_path)
                self.save_repos(repos)
                print(f"Added repository (replacing existing): {repo_path}")
            else:
                print(f"Repository with name '{repo_name}' already exists:")
                for existing_path in existing_repos_with_same_name:
                    print(f"  {existing_path}")
                print("Use --force to replace existing repository")
        else:
            repos['repos'].insert(0, repo_path)  # Add to front for priority
            self.save_repos(repos)
            print(f"Added repository: {repo_path}")

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

    def remove_repo_by_name(self, repo_name: str):
        """
        Remove all repositories with the given name from the repos configuration.

        :param repo_name: Name of repository to remove
        :return: Number of repositories removed
        """
        repos = self.repos.copy()
        initial_count = len(repos['repos'])
        removed_repos = []

        # Find all repositories with matching name
        remaining_repos = []
        for repo_path in repos['repos']:
            if Path(repo_path).name == repo_name:
                removed_repos.append(repo_path)
            else:
                remaining_repos.append(repo_path)

        if removed_repos:
            repos['repos'] = remaining_repos
            self.save_repos(repos)

            print(f"Removed {len(removed_repos)} repository(ies) named '{repo_name}':")
            for repo_path in removed_repos:
                print(f"  - {repo_path}")
        else:
            print(f"No repositories found with name '{repo_name}'")

        return len(removed_repos)

    def cleanup_nonexistent_repos(self):
        """Remove any repositories from configuration that no longer exist on disk"""
        repos = self.repos.copy()
        initial_count = len(repos['repos'])
        removed_repos = []

        # Filter out non-existent repositories
        existing_repos = []
        for repo_path in repos['repos']:
            if Path(repo_path).exists():
                existing_repos.append(repo_path)
            else:
                removed_repos.append(repo_path)

        # Update repos if any were removed
        if removed_repos:
            repos['repos'] = existing_repos
            self.save_repos(repos)

            print(f"Automatically removed {len(removed_repos)} non-existent repositories:")
            for repo_path in removed_repos:
                print(f"  - {repo_path}")

        return len(removed_repos)

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
        """Get the config directory for a specific pipeline"""
        return Path(self.config_dir) / 'pipelines' / pipeline_name

    def get_pipeline_shared_dir(self, pipeline_name: str) -> Path:
        """Get the shared directory for a specific pipeline"""
        return Path(self.shared_dir) / pipeline_name

    def get_pipeline_private_dir(self, pipeline_name: str) -> Path:
        """Get the private directory for a specific pipeline"""
        return Path(self.private_dir) / pipeline_name

    def get_current_pipeline_dir(self) -> Optional[Path]:
        """Get the config directory for the current pipeline"""
        current_pipeline = self.config.get('current_pipeline')
        if current_pipeline:
            return self.get_pipeline_dir(current_pipeline)
        return None

    def get_current_pipeline_shared_dir(self) -> Optional[Path]:
        """Get the shared directory for the current pipeline"""
        current_pipeline = self.config.get('current_pipeline')
        if current_pipeline:
            return self.get_pipeline_shared_dir(current_pipeline)
        return None

    def get_current_pipeline_private_dir(self) -> Optional[Path]:
        """Get the private directory for the current pipeline"""
        current_pipeline = self.config.get('current_pipeline')
        if current_pipeline:
            return self.get_pipeline_private_dir(current_pipeline)
        return None

    def set_current_pipeline(self, pipeline_name: str):
        """Set the current active pipeline"""
        config = self.config.copy()
        config['current_pipeline'] = pipeline_name
        self.save_config(config)

    def get_current_pipeline(self) -> Optional[str]:
        """Get the name of the current active pipeline"""
        return self.config.get('current_pipeline')

    def set_current_module(self, module_name: Optional[str]):
        """Set the current active module"""
        config = self.config.copy()
        config['current_module'] = module_name
        self.save_config(config)

    def get_current_module(self) -> Optional[str]:
        """Get the name of the current active module"""
        return self.config.get('current_module')

    def get_pipelines_dir(self) -> Path:
        """Get the directory where all pipelines are stored"""
        config_dir = Path(self.config['config_dir'])
        return config_dir / 'pipelines'

    def get_builtin_repo_path(self) -> Path:
        """Get path to builtin repository"""
        # First check if builtin repo is registered in repos
        for repo_path_str in self.repos['repos']:
            repo_path = Path(repo_path_str)
            if repo_path.name == 'builtin' and repo_path.exists():
                return repo_path

        # Fall back to builtin repo installed to ~/.ppi-jarvis/builtin
        user_builtin = self.jarvis_root / 'builtin'
        if user_builtin.exists():
            return user_builtin

        # Fall back to builtin repo in the same directory as this file (development)
        dev_builtin = Path(__file__).parent.parent.parent / 'builtin'
        if dev_builtin.exists():
            return dev_builtin

        # Fall back to installed package location
        try:
            import importlib.util
            import importlib.metadata
            import site

            # Method 1: Try to find builtin package directly
            try:
                import builtin
                builtin_module_path = Path(builtin.__file__).parent
                if builtin_module_path.exists():
                    return builtin_module_path
            except ImportError:
                pass

            # Method 2: Look for builtin in installed package files
            try:
                dist = importlib.metadata.distribution('jarvis_cd')
                if hasattr(dist, 'files') and dist.files:
                    for file in dist.files:
                        if 'builtin' in str(file) and str(file).endswith('builtin/__init__.py'):
                            # Get the actual installation path
                            for path in site.getsitepackages() + [site.getusersitepackages()]:
                                if path:
                                    candidate = Path(path) / file.parent
                                    if candidate.exists():
                                        return candidate
            except Exception:
                pass

            # Method 3: Search in site-packages
            for path in site.getsitepackages() + [site.getusersitepackages()]:
                if path:
                    builtin_path = Path(path) / 'builtin'
                    if builtin_path.exists() and (builtin_path / '__init__.py').exists():
                        return builtin_path

        except Exception:
            pass

        # Default fallback
        return user_builtin

    def find_package(self, pkg_name: str) -> Optional[str]:
        """
        Find a package in registered repositories.
        Returns the full import path if found.
        Searches repositories in order, respecting priority.
        """
        # Check all registered repos in order (builtin is already in the list)
        for repo_path in self.repos['repos']:
            repo_name = Path(repo_path).name
            if self._check_package_exists(repo_path, repo_name, pkg_name):
                return f'{repo_name}.{pkg_name}'

        return None

    def _check_package_exists(self, repo_path: str, repo_name: str, pkg_name: str) -> bool:
        """Check if a package exists in a repository"""
        # Try both package.py and pkg.py (legacy naming)
        package_file = Path(repo_path) / repo_name / pkg_name / 'package.py'
        if package_file.exists():
            return True

        # Check for legacy pkg.py naming
        legacy_package_file = Path(repo_path) / repo_name / pkg_name / 'pkg.py'
        return legacy_package_file.exists()

    def is_initialized(self) -> bool:
        """Check if Jarvis has been initialized"""
        return self.config_file.exists()
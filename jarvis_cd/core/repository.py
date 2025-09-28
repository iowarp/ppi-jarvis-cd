import os
import shutil
from pathlib import Path
from typing import Dict, Any, List
from jarvis_cd.core.config import JarvisConfig


class RepositoryManager:
    """
    Manages Jarvis repositories - adding, removing, listing, and creating packages.
    """
    
    def __init__(self, jarvis_config: JarvisConfig):
        """
        Initialize repository manager.
        
        :param jarvis_config: Jarvis configuration manager
        """
        self.jarvis_config = jarvis_config
        
    def add_repository(self, repo_path: str, force: bool = False):
        """
        Add a repository to Jarvis.
        
        :param repo_path: Path to repository directory
        :param force: Force overwrite if repository already exists
        """
        repo_path = Path(repo_path).absolute()
        
        if not repo_path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {repo_path}")
            
        if not repo_path.is_dir():
            raise ValueError(f"Repository path is not a directory: {repo_path}")
            
        # Check if it looks like a valid repository
        repo_name = repo_path.name
        expected_subdir = repo_path / repo_name
        
        if not expected_subdir.exists():
            print(f"Warning: Repository {repo_path} does not contain expected subdirectory {repo_name}")
            print("Expected structure: repo_name/repo_name/package_name/package.py")
            
        self.jarvis_config.add_repo(str(repo_path), force=force)
        
    def remove_repository(self, repo_path: str):
        """
        Remove a repository from Jarvis.
        
        :param repo_path: Path to repository directory
        """
        repo_path = Path(repo_path).absolute()
        self.jarvis_config.remove_repo(str(repo_path))
        
    def list_repositories(self):
        """List all registered repositories"""
        repos = self.jarvis_config.repos['repos']
        builtin_path = self.jarvis_config.get_builtin_repo_path()
        builtin_path_str = str(builtin_path)
        
        print("Registered repositories:")
        if not repos:
            print("  No repositories registered")
        else:
            repo_count = 0
            for repo_path in repos:
                repo_name = Path(repo_path).name
                exists = "✓" if Path(repo_path).exists() else "✗"
                
                # Check if this is the builtin repository
                if repo_path == builtin_path_str:
                    print(f"  {repo_count+1}. {repo_name} ({repo_path}) {exists} [builtin]")
                else:
                    print(f"  {repo_count+1}. {repo_name} ({repo_path}) {exists}")
                repo_count += 1
                
        # Only show separate builtin entry if it's not in the registered repos
        if builtin_path_str not in repos:
            builtin_exists = "✓" if builtin_path.exists() else "✗"
            print(f"  Built-in: builtin ({builtin_path}) {builtin_exists}")
        
    def create_package(self, package_name: str, package_type: str):
        """
        Create a new package in the first available repository.
        
        :param package_name: Name of package to create
        :param package_type: Type of package (service, app, interceptor)
        """
        if package_type not in ['service', 'app', 'interceptor']:
            raise ValueError(f"Invalid package type: {package_type}. Must be service, app, or interceptor")
            
        repos = self.jarvis_config.repos['repos']
        if not repos:
            raise ValueError("No repositories registered. Add a repository first with 'jarvis repo add'")
            
        # Use the first repository
        repo_path = Path(repos[0])
        repo_name = repo_path.name
        
        if not repo_path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {repo_path}")
            
        # Create package directory structure
        package_dir = repo_path / repo_name / package_name
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # Create package.py file
        package_file = package_dir / 'package.py'
        
        # Generate package template based on type
        template_content = self._generate_package_template(package_name, package_type)
        
        with open(package_file, 'w') as f:
            f.write(template_content)
            
        print(f"Created {package_type} package: {package_name}")
        print(f"Location: {package_file}")
        
    def _generate_package_template(self, package_name: str, package_type: str) -> str:
        """
        Generate package template code based on package type.
        
        :param package_name: Name of the package
        :param package_type: Type of package (service, app, interceptor)
        :return: Template code as string
        """
        class_name = package_name.capitalize()
        
        if package_type == 'service':
            return self._generate_service_template(class_name, package_name)
        elif package_type == 'app':
            return self._generate_app_template(class_name, package_name)
        elif package_type == 'interceptor':
            return self._generate_interceptor_template(class_name, package_name)
        else:
            raise ValueError(f"Unknown package type: {package_type}")
            
    def _generate_service_template(self, class_name: str, package_name: str) -> str:
        """Generate service package template"""
        return f'''"""
{class_name} service package for Jarvis-CD.
This is a long-running service that needs to be manually stopped.
"""
from jarvis_cd.basic.pkg import Service


class {class_name}(Service):
    """
    {class_name} service implementation.
    """
    
    def _init(self):
        """
        Initialize service-specific variables.
        Don't assume that self.config is initialized.
        """
        self.port = None
        self.daemon_process = None
        
    def _configure_menu(self):
        """
        Create a CLI menu for the configurator method.
        
        :return: List of argument dictionaries
        """
        return [
            {{
                'name': 'port',
                'msg': 'The port to listen on',
                'type': int,
                'default': 8080
            }},
            {{
                'name': 'config_file',
                'msg': 'Path to configuration file',
                'type': str,
                'default': None
            }}
        ]
        
    def configure(self, **kwargs):
        """
        Configure the service with given parameters.
        
        :param kwargs: Configuration parameters
        """
        self.update_config(kwargs, rebuild=False)
        
        # Generate service-specific configuration files
        config_data = {{
            'port': self.config['port'],
            'service_name': '{package_name}'
        }}
        
        # Save configuration to shared directory
        import yaml
        config_file = f'{{self.shared_dir}}/{package_name}_config.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
            
        print(f"Generated {package_name} configuration: {{config_file}}")
        
    def start(self):
        """
        Start the {package_name} service.
        """
        print(f"Starting {package_name} service on port {{self.config['port']}}")
        
        # Example service startup - replace with actual service commands
        # self.daemon_process = subprocess.Popen([
        #     '{package_name}_daemon',
        #     '--port', str(self.config['port']),
        #     '--config', f'{{self.shared_dir}}/{package_name}_config.yaml'
        # ])
        
        # Sleep to ensure service starts up
        import time
        time.sleep(self.config.get('sleep', 2))
        print(f"{package_name} service started")
        
    def stop(self):
        """
        Stop the {package_name} service.
        """
        print(f"Stopping {package_name} service")
        
        # Example service shutdown - replace with actual service commands
        # if self.daemon_process:
        #     self.daemon_process.terminate()
        #     self.daemon_process.wait()
        #     self.daemon_process = None
        
        print(f"{package_name} service stopped")
        
    def kill(self):
        """
        Force kill the {package_name} service.
        """
        print(f"Force killing {package_name} service")
        
        # Example force kill - replace with actual kill commands
        # if self.daemon_process:
        #     self.daemon_process.kill()
        #     self.daemon_process = None
        
        print(f"{package_name} service killed")
        
    def clean(self):
        """
        Clean up all {package_name} data and configuration.
        """
        print(f"Cleaning {package_name} service data")
        
        # Remove configuration files
        import os
        config_file = f'{{self.shared_dir}}/{package_name}_config.yaml'
        if os.path.exists(config_file):
            os.remove(config_file)
            
        # Remove any data directories or files
        # os.system(f'rm -rf {{self.private_dir}}/{package_name}_data')
        
        print(f"{package_name} service cleaned")
        
    def status(self):
        """
        Check the status of the {package_name} service.
        
        :return: Service status string
        """
        # Example status check - replace with actual status logic
        # if self.daemon_process and self.daemon_process.poll() is None:
        #     return "running"
        # else:
        #     return "stopped"
        
        return "unknown"
'''
        
    def _generate_app_template(self, class_name: str, package_name: str) -> str:
        """Generate application package template"""
        return f'''"""
{class_name} application package for Jarvis-CD.
This is an application that runs and completes automatically.
"""
from jarvis_cd.basic.pkg import Application


class {class_name}(Application):
    """
    {class_name} application implementation.
    """
    
    def _init(self):
        """
        Initialize application-specific variables.
        Don't assume that self.config is initialized.
        """
        self.input_file = None
        self.output_file = None
        self.nprocs = None
        
    def _configure_menu(self):
        """
        Create a CLI menu for the configurator method.
        
        :return: List of argument dictionaries
        """
        return [
            {{
                'name': 'input_file',
                'msg': 'Path to input file',
                'type': str,
                'default': '/tmp/{package_name}_input.dat'
            }},
            {{
                'name': 'output_file',
                'msg': 'Path to output file',
                'type': str,
                'default': '/tmp/{package_name}_output.dat'
            }},
            {{
                'name': 'nprocs',
                'msg': 'Number of processes',
                'type': int,
                'default': 1
            }},
            {{
                'name': 'ppn',
                'msg': 'Processes per node',
                'type': int,
                'default': 1
            }}
        ]
        
    def configure(self, **kwargs):
        """
        Configure the application with given parameters.
        
        :param kwargs: Configuration parameters
        """
        self.update_config(kwargs, rebuild=False)
        
        # Validate configuration
        if self.config['nprocs'] <= 0:
            raise ValueError("Number of processes must be positive")
            
        print(f"Configured {package_name} application:")
        print(f"  Input: {{self.config['input_file']}}")
        print(f"  Output: {{self.config['output_file']}}")
        print(f"  Processes: {{self.config['nprocs']}}")
        
    def start(self):
        """
        Run the {package_name} application.
        """
        print(f"Running {package_name} application")
        
        # Prepare input data if needed
        self._prepare_input()
        
        # Example application execution - replace with actual commands
        # cmd = [
        #     '{package_name}',
        #     '--input', self.config['input_file'],
        #     '--output', self.config['output_file']
        # ]
        
        # Example MPI execution:
        # from jarvis_util import MpiExecInfo, Exec
        # Exec(' '.join(cmd),
        #      MpiExecInfo(env=self.mod_env,
        #                  hostfile=self.jarvis.hostfile,
        #                  nprocs=self.config['nprocs'],
        #                  ppn=self.config['ppn']))
        
        print(f"{package_name} application completed")
        
    def stop(self):
        """
        Stop the application (usually not needed for apps).
        """
        print(f"Stopping {package_name} application")
        
    def clean(self):
        """
        Clean up application data and temporary files.
        """
        print(f"Cleaning {package_name} application data")
        
        # Remove output files
        import os
        if os.path.exists(self.config['output_file']):
            os.remove(self.config['output_file'])
            
        # Remove any temporary files
        # os.system(f'rm -f {{self.config["output_file"]}}*')
        
        print(f"{package_name} application cleaned")
        
    def _prepare_input(self):
        """
        Prepare input data for the application.
        """
        import os
        
        input_file = self.config['input_file']
        
        # Create input directory if needed
        os.makedirs(os.path.dirname(input_file), exist_ok=True)
        
        # Generate or copy input data
        if not os.path.exists(input_file):
            print(f"Generating input file: {{input_file}}")
            with open(input_file, 'w') as f:
                f.write(f"# {package_name} input data\\n")
                f.write(f"# Generated by Jarvis-CD\\n")
'''
        
    def _generate_interceptor_template(self, class_name: str, package_name: str) -> str:
        """Generate interceptor package template"""
        return f'''"""
{class_name} interceptor package for Jarvis-CD.
This modifies environment variables to intercept system/library calls.
"""
from jarvis_cd.basic.pkg import Interceptor


class {class_name}(Interceptor):
    """
    {class_name} interceptor implementation.
    """
    
    def _init(self):
        """
        Initialize interceptor-specific variables.
        Don't assume that self.config is initialized.
        """
        self.library_path = None
        
    def _configure_menu(self):
        """
        Create a CLI menu for the configurator method.
        
        :return: List of argument dictionaries
        """
        return [
            {{
                'name': 'library_name',
                'msg': 'Name of the library to intercept',
                'type': str,
                'default': '{package_name}_intercept'
            }},
            {{
                'name': 'enable_logging',
                'msg': 'Enable interception logging',
                'type': bool,
                'default': False
            }}
        ]
        
    def configure(self, **kwargs):
        """
        Configure the interceptor with given parameters.
        
        :param kwargs: Configuration parameters
        """
        self.update_config(kwargs, rebuild=False)
        
        # Find the interception library
        library_name = self.config['library_name']
        self.config['library_path'] = self.find_library(library_name)
        
        if self.config['library_path'] is None:
            raise Exception(f'Could not find {{library_name}} library')
            
        print(f'Found {{library_name}} library at {{self.config["library_path"]}}')
        
        # Set up logging if enabled
        if self.config['enable_logging']:
            self.config['log_file'] = f'{{self.private_dir}}/{package_name}_intercept.log'
            print(f'Interception logging enabled: {{self.config["log_file"]}}')
        
    def modify_env(self):
        """
        Modify the environment to enable interception.
        """
        # Add library to LD_PRELOAD
        self.prepend_env('LD_PRELOAD', self.config['library_path'])
        
        # Set up logging environment if enabled
        if self.config['enable_logging']:
            self.setenv('{package_name.upper()}_LOG_FILE', self.config['log_file'])
            self.setenv('{package_name.upper()}_LOG_LEVEL', 'INFO')
            
        print(f"Environment modified for {package_name} interception")
        print(f"LD_PRELOAD: {{self.mod_env.get('LD_PRELOAD', '')}}")
'''

    def list_packages_in_repo(self, repo_path: str) -> List[str]:
        """
        List all packages in a repository.
        
        :param repo_path: Path to repository
        :return: List of package names
        """
        repo_path = Path(repo_path)
        repo_name = repo_path.name
        packages_dir = repo_path / repo_name
        
        if not packages_dir.exists():
            return []
            
        packages = []
        for item in packages_dir.iterdir():
            if item.is_dir() and (item / 'package.py').exists():
                packages.append(item.name)
                
        return sorted(packages)
        
    def find_all_packages(self) -> Dict[str, List[str]]:
        """
        Find all packages in all registered repositories.
        
        :return: Dictionary mapping repo names to package lists
        """
        all_packages = {}
        
        # Check builtin repository
        builtin_path = self.jarvis_config.get_builtin_repo_path()
        if builtin_path.exists():
            packages = self.list_packages_in_repo(str(builtin_path))
            if packages:
                all_packages['builtin'] = packages
                
        # Check registered repositories
        for repo_path in self.jarvis_config.repos['repos']:
            repo_name = Path(repo_path).name
            if Path(repo_path).exists():
                packages = self.list_packages_in_repo(repo_path)
                if packages:
                    all_packages[repo_name] = packages
                    
        return all_packages
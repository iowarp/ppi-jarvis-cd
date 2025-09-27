import sys
import os
from pathlib import Path
from jarvis_cd.util.argparse import ArgParse
from jarvis_cd.core.config import JarvisConfig
from jarvis_cd.core.pipeline import PipelineManager
from jarvis_cd.core.repository import RepositoryManager
from jarvis_cd.core.package import PackageManager


class JarvisCLI(ArgParse):
    """
    Main Jarvis CLI using the custom ArgParse class.
    Provides commands for initialization, pipeline management, repository management, etc.
    """
    
    def __init__(self):
        super().__init__()
        self.jarvis_config = None
        self.pipeline_manager = None
        self.repo_manager = None
        self.pkg_manager = None
        
    def define_options(self):
        """Define the complete Jarvis CLI command structure"""
        
        # Main menu (empty command for global options)
        self.add_menu('')
        self.add_cmd('', keep_remainder=True)
        self.add_args([
            {
                'name': 'help',
                'msg': 'Show help information',
                'type': bool,
                'default': False,
                'aliases': ['h']
            }
        ])
        
        # Init command
        self.add_menu('init', msg="Initialize Jarvis configuration")
        self.add_cmd('init', msg="Initialize Jarvis configuration directories", keep_remainder=False)
        self.add_args([
            {
                'name': 'config_dir',
                'msg': 'Configuration directory',
                'type': str,
                'pos': True,
                'default': '~/.jarvis/config',
                'class': 'dirs',
                'rank': 0
            },
            {
                'name': 'private_dir', 
                'msg': 'Private data directory',
                'type': str,
                'pos': True,
                'default': '~/.jarvis/private',
                'class': 'dirs',
                'rank': 1
            },
            {
                'name': 'shared_dir',
                'msg': 'Shared data directory', 
                'type': str,
                'pos': True,
                'default': '~/.jarvis/shared',
                'class': 'dirs',
                'rank': 2
            }
        ])
        
        # Pipeline commands
        self.add_menu('ppl', msg="Pipeline management commands")
        
        self.add_cmd('ppl create', msg="Create a new pipeline", aliases=['ppl c'])
        self.add_args([
            {
                'name': 'pipeline_name',
                'msg': 'Name of the pipeline to create',
                'type': str,
                'required': True,
                'pos': True
            }
        ])
        
        self.add_cmd('ppl append', msg="Add a package to current pipeline", aliases=['ppl a'])
        self.add_args([
            {
                'name': 'package_spec',
                'msg': 'Package specification (repo.pkg or just pkg)',
                'type': str,
                'required': True,
                'pos': True,
                'class': 'pkg',
                'rank': 0
            },
            {
                'name': 'package_alias',
                'msg': 'Alias for the package in pipeline',
                'type': str,
                'pos': True,
                'class': 'pkg', 
                'rank': 1
            }
        ])
        
        self.add_cmd('ppl run', msg="Run a pipeline", aliases=['ppl r'])
        self.add_args([
            {
                'name': 'pipeline_file',
                'msg': 'Pipeline YAML file to run',
                'type': str,
                'pos': True
            },
            {
                'name': 'load_type',
                'msg': 'Type of pipeline to load',
                'type': str,
                'pos': True,
                'default': 'current'
            }
        ])
        
        self.add_cmd('ppl start', msg="Start current pipeline")
        self.add_args([])
        
        self.add_cmd('ppl stop', msg="Stop current pipeline")
        self.add_args([])
        
        self.add_cmd('ppl kill', msg="Force kill current pipeline")
        self.add_args([])
        
        self.add_cmd('ppl clean', msg="Clean current pipeline data")
        self.add_args([])
        
        self.add_cmd('ppl status', msg="Show current pipeline status")
        self.add_args([])
        
        self.add_cmd('ppl load', msg="Load a pipeline from file")
        self.add_args([
            {
                'name': 'load_type',
                'msg': 'Type of pipeline to load (yaml)',
                'type': str,
                'required': True,
                'pos': True
            },
            {
                'name': 'pipeline_file',
                'msg': 'Pipeline file to load',
                'type': str,
                'required': True,
                'pos': True
            }
        ])
        
        self.add_cmd('ppl update', msg="Update current pipeline")
        self.add_args([
            {
                'name': 'update_type',
                'msg': 'Type of update (yaml)',
                'type': str,
                'pos': True,
                'default': 'yaml'
            }
        ])
        
        # Repository commands
        self.add_menu('repo', msg="Repository management commands")
        
        self.add_cmd('repo add', msg="Add a repository to Jarvis")
        self.add_args([
            {
                'name': 'repo_path',
                'msg': 'Path to repository directory',
                'type': str,
                'required': True,
                'pos': True
            }
        ])
        
        self.add_cmd('repo remove', msg="Remove a repository from Jarvis", aliases=['repo rm'])
        self.add_args([
            {
                'name': 'repo_path',
                'msg': 'Path to repository directory',
                'type': str,
                'required': True,
                'pos': True
            }
        ])
        
        self.add_cmd('repo list', msg="List all registered repositories", aliases=['repo ls'])
        self.add_args([])
        
        self.add_cmd('repo create', msg="Create a new package in repository")
        self.add_args([
            {
                'name': 'package_name',
                'msg': 'Name of package to create',
                'type': str,
                'required': True,
                'pos': True,
                'class': 'pkg',
                'rank': 0
            },
            {
                'name': 'package_type',
                'msg': 'Type of package (service, app, interceptor)',
                'type': str,
                'required': True,
                'pos': True,
                'choices': ['service', 'app', 'interceptor'],
                'class': 'pkg',
                'rank': 1
            }
        ])
        
        # Package commands
        self.add_menu('pkg', msg="Package management commands")
        
        self.add_cmd('pkg configure', msg="Configure a package", aliases=['pkg conf'])
        self.add_args([
            {
                'name': 'package_spec',
                'msg': 'Package to configure (pkg or pipeline.pkg)',
                'type': str,
                'required': True,
                'pos': True
            }
        ])
        
        # Set hostfile command
        self.add_menu('hostfile', msg="Hostfile management")
        self.add_cmd('hostfile set', msg="Set the hostfile for deployments")
        self.add_args([
            {
                'name': 'hostfile_path',
                'msg': 'Path to hostfile',
                'type': str,
                'required': True,
                'pos': True
            }
        ])
        
    def _ensure_initialized(self):
        """Ensure Jarvis is initialized before running commands"""
        if self.jarvis_config is None:
            self.jarvis_config = JarvisConfig()
            
        if not self.jarvis_config.is_initialized():
            print("Error: Jarvis not initialized. Run 'jarvis init' first.")
            sys.exit(1)
            
        # Initialize managers
        if self.pipeline_manager is None:
            self.pipeline_manager = PipelineManager(self.jarvis_config)
        if self.repo_manager is None:
            self.repo_manager = RepositoryManager(self.jarvis_config)
        if self.pkg_manager is None:
            self.pkg_manager = PackageManager(self.jarvis_config)
    
    def main_menu(self):
        """Handle main menu / help"""
        if self.kwargs.get('help', False) or not self.remainder:
            self._show_help()
        else:
            print(f"Unknown arguments: {' '.join(self.remainder)}")
            self._show_help()
            
    def _show_help(self):
        """Show help information"""
        print("Jarvis-CD: Unified platform for deploying applications and benchmarks")
        print()
        self.print_general_help()
    
    # Command handlers
    def init(self):
        """Initialize Jarvis configuration"""
        config_dir = os.path.expanduser(self.kwargs['config_dir'])
        private_dir = os.path.expanduser(self.kwargs['private_dir'])
        shared_dir = os.path.expanduser(self.kwargs['shared_dir'])
        
        jarvis_config = JarvisConfig()
        jarvis_config.initialize(config_dir, private_dir, shared_dir)
        
    def ppl_create(self):
        """Create a new pipeline"""
        self._ensure_initialized()
        pipeline_name = self.kwargs['pipeline_name']
        self.pipeline_manager.create_pipeline(pipeline_name)
        
    def ppl_append(self):
        """Append package to current pipeline"""
        self._ensure_initialized()
        package_spec = self.kwargs['package_spec']
        package_alias = self.kwargs.get('package_alias')
        self.pipeline_manager.append_package(package_spec, package_alias)
        
    def ppl_run(self):
        """Run pipeline"""
        self._ensure_initialized()
        pipeline_file = self.kwargs.get('pipeline_file')
        load_type = self.kwargs.get('load_type', 'current')
        
        if pipeline_file and load_type != 'current':
            # Load and run pipeline file
            self.pipeline_manager.load_pipeline(load_type, pipeline_file)
            
        self.pipeline_manager.run_pipeline()
        
    def ppl_start(self):
        """Start current pipeline"""
        self._ensure_initialized()
        self.pipeline_manager.start_pipeline()
        
    def ppl_stop(self):
        """Stop current pipeline"""
        self._ensure_initialized()
        self.pipeline_manager.stop_pipeline()
        
    def ppl_kill(self):
        """Kill current pipeline"""
        self._ensure_initialized()
        self.pipeline_manager.kill_pipeline()
        
    def ppl_clean(self):
        """Clean current pipeline"""
        self._ensure_initialized()
        self.pipeline_manager.clean_pipeline()
        
    def ppl_status(self):
        """Show pipeline status"""
        self._ensure_initialized()
        self.pipeline_manager.show_status()
        
    def ppl_load(self):
        """Load pipeline from file"""
        self._ensure_initialized()
        load_type = self.kwargs['load_type']
        pipeline_file = self.kwargs['pipeline_file']
        self.pipeline_manager.load_pipeline(load_type, pipeline_file)
        
    def ppl_update(self):
        """Update pipeline from last loaded file"""
        self._ensure_initialized()
        update_type = self.kwargs.get('update_type', 'yaml')
        self.pipeline_manager.update_pipeline(update_type)
        
    def repo_add(self):
        """Add repository"""
        self._ensure_initialized()
        repo_path = self.kwargs['repo_path']
        self.repo_manager.add_repository(repo_path)
        
    def repo_remove(self):
        """Remove repository"""
        self._ensure_initialized()
        repo_path = self.kwargs['repo_path']
        self.repo_manager.remove_repository(repo_path)
        
    def repo_list(self):
        """List repositories"""
        self._ensure_initialized()
        self.repo_manager.list_repositories()
        
    def repo_create(self):
        """Create new package in repository"""
        self._ensure_initialized()
        package_name = self.kwargs['package_name']
        package_type = self.kwargs['package_type']
        self.repo_manager.create_package(package_name, package_type)
        
    def pkg_configure(self):
        """Configure package"""
        self._ensure_initialized()
        package_spec = self.kwargs['package_spec']
        
        # Extract additional configuration arguments from remainder
        config_args = {}
        for arg in self.remainder:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')  # Remove leading dashes
                config_args[key] = value
                
        self.pkg_manager.configure_package(package_spec, config_args)
        
    def hostfile_set(self):
        """Set hostfile"""
        self._ensure_initialized()
        hostfile_path = self.kwargs['hostfile_path']
        self.jarvis_config.set_hostfile(hostfile_path)


def main():
    """Main entry point for jarvis CLI"""
    try:
        cli = JarvisCLI()
        cli.define_options()
        result = cli.parse(sys.argv[1:])
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
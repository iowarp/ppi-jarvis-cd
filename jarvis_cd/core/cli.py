import sys
import os
from pathlib import Path
from jarvis_cd.util.argparse import ArgParse
from jarvis_cd.core.config import JarvisConfig, Jarvis
from jarvis_cd.core.pipeline import PipelineManager
from jarvis_cd.core.pipeline_index import PipelineIndexManager
from jarvis_cd.core.repository import RepositoryManager
from jarvis_cd.core.package import PackageManager
from jarvis_cd.core.environment import EnvironmentManager
from jarvis_cd.core.resource_graph import ResourceGraphManager


class JarvisCLI(ArgParse):
    """
    Main Jarvis CLI using the custom ArgParse class.
    Provides commands for initialization, pipeline management, repository management, etc.
    """
    
    def __init__(self):
        super().__init__()
        self.jarvis_config = None
        self.pipeline_manager = None
        self.pipeline_index_manager = None
        self.repo_manager = None
        self.pkg_manager = None
        self.env_manager = None
        self.rg_manager = None
        
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
                'name': 'load_type',
                'msg': 'Type of pipeline to load (yaml) or current',
                'type': str,
                'pos': True,
                'default': 'current'
            },
            {
                'name': 'pipeline_file',
                'msg': 'Pipeline YAML file to run (required if load_type is yaml)',
                'type': str,
                'pos': True
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
        
        self.add_cmd('ppl list', msg="List all pipelines", aliases=['ppl ls'])
        self.add_args([])
        
        self.add_cmd('ppl print', msg="Print current pipeline configuration")
        self.add_args([])
        
        self.add_cmd('ppl rm', msg="Remove a package from current pipeline", aliases=['ppl remove'])
        self.add_args([
            {
                'name': 'package_spec',
                'msg': 'Package to remove (pkg_id or pipeline.pkg_id)',
                'type': str,
                'required': True,
                'pos': True
            }
        ])
        
        # Pipeline environment commands - need to add menu first
        self.add_menu('ppl env', msg="Pipeline environment management")
        
        self.add_cmd('ppl env build', msg="Build environment for current pipeline", keep_remainder=True)
        self.add_args([])
        
        self.add_cmd('ppl env copy', msg="Copy named environment to current pipeline")
        self.add_args([
            {
                'name': 'env_name',
                'msg': 'Name of environment to copy',
                'type': str,
                'required': True,
                'pos': True
            }
        ])
        
        self.add_cmd('ppl env show', msg="Show current pipeline environment")
        self.add_args([])
        
        # Pipeline index commands
        self.add_menu('ppl index', msg="Pipeline index management")
        
        self.add_cmd('ppl index load', msg="Load a pipeline script from an index")
        self.add_args([
            {
                'name': 'index_query',
                'msg': 'Index query (e.g., repo.subdir.script)',
                'type': str,
                'required': True,
                'pos': True
            }
        ])
        
        self.add_cmd('ppl index copy', msg="Copy a pipeline script from an index")
        self.add_args([
            {
                'name': 'index_query',
                'msg': 'Index query (e.g., repo.subdir.script)',
                'type': str,
                'required': True,
                'pos': True
            },
            {
                'name': 'output',
                'msg': 'Output directory or file (optional)',
                'type': str,
                'required': False,
                'pos': True
            }
        ])
        
        self.add_cmd('ppl index list', msg="List available pipeline scripts in indexes", aliases=['ppl index ls'])
        self.add_args([
            {
                'name': 'repo_name',
                'msg': 'Repository name to list (optional)',
                'type': str,
                'required': False,
                'pos': True
            }
        ])
        
        # Change directory (switch current pipeline)
        self.add_cmd('cd', msg="Change current pipeline")
        self.add_args([
            {
                'name': 'pipeline_name',
                'msg': 'Name of pipeline to switch to',
                'type': str,
                'required': True,
                'pos': True
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
            },
            {
                'name': 'force',
                'msg': 'Force overwrite if repository already exists',
                'type': bool,
                'default': False,
                'aliases': ['f']
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
        
        # Environment commands
        self.add_menu('env', msg="Named environment management")
        
        self.add_cmd('env build', msg="Build a named environment", keep_remainder=True)
        self.add_args([
            {
                'name': 'env_name',
                'msg': 'Name of environment to create',
                'type': str,
                'required': True,
                'pos': True
            }
        ])
        
        self.add_cmd('env list', msg="List all named environments", aliases=['env ls'])
        self.add_args([])
        
        self.add_cmd('env show', msg="Show a named environment")
        self.add_args([
            {
                'name': 'env_name',
                'msg': 'Name of environment to show',
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
        
        # Resource graph commands
        self.add_menu('rg', msg="Resource graph management")
        
        self.add_cmd('rg build', msg="Build resource graph from hostfile")
        self.add_args([
            {
                'name': 'no_benchmark',
                'msg': 'Skip performance benchmarking',
                'type': bool,
                'default': False
            },
            {
                'name': 'duration',
                'msg': 'Benchmark duration in seconds',
                'type': int,
                'default': 25
            }
        ])
        
        self.add_cmd('rg show', msg="Show resource graph summary")
        self.add_args([])
        
        self.add_cmd('rg nodes', msg="List nodes in resource graph")
        self.add_args([])
        
        self.add_cmd('rg node', msg="Show detailed node information")
        self.add_args([
            {
                'name': 'hostname',
                'msg': 'Hostname to show details for',
                'type': str,
                'required': True,
                'pos': True
            }
        ])
        
        self.add_cmd('rg filter', msg="Filter storage by device type")
        self.add_args([
            {
                'name': 'dev_type',
                'msg': 'Device type to filter by (ssd, hdd, etc.)',
                'type': str,
                'required': True,
                'pos': True
            }
        ])
        
        self.add_cmd('rg load', msg="Load resource graph from file")
        self.add_args([
            {
                'name': 'file_path',
                'msg': 'Path to resource graph file',
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
            
        # Initialize Jarvis singleton if not already done
        try:
            Jarvis.get_instance()
        except RuntimeError:
            # Singleton not initialized, initialize it now
            config = self.jarvis_config.config
            config_dir = config.get('config_dir', str(self.jarvis_config.jarvis_root))
            private_dir = config.get('private_dir', str(self.jarvis_config.jarvis_root / 'private'))
            shared_dir = config.get('shared_dir', str(self.jarvis_config.jarvis_root / 'shared'))
            Jarvis.initialize(self.jarvis_config, config_dir, private_dir, shared_dir)
            
        # Initialize managers
        if self.pipeline_manager is None:
            self.pipeline_manager = PipelineManager(self.jarvis_config)
        if self.repo_manager is None:
            self.repo_manager = RepositoryManager(self.jarvis_config)
        if self.pkg_manager is None:
            self.pkg_manager = PackageManager(self.jarvis_config)
        if self.env_manager is None:
            self.env_manager = EnvironmentManager(self.jarvis_config)
        if self.rg_manager is None:
            self.rg_manager = ResourceGraphManager(self.jarvis_config)
        if self.pipeline_index_manager is None:
            self.pipeline_index_manager = PipelineIndexManager(self.jarvis_config)
    
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
        
        # Initialize Jarvis singleton
        Jarvis.initialize(jarvis_config, config_dir, private_dir, shared_dir)
        print(f"Jarvis initialized successfully!")
        print(f"Config dir: {config_dir}")
        print(f"Private dir: {private_dir}")
        print(f"Shared dir: {shared_dir}")
        
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
        load_type = self.kwargs.get('load_type', 'current')
        pipeline_file = self.kwargs.get('pipeline_file')
        
        if load_type == 'yaml':
            if not pipeline_file:
                raise ValueError("Pipeline file is required when load_type is 'yaml'")
            # Load and run pipeline file in one command
            self.pipeline_manager.run_pipeline(load_type, pipeline_file)
        else:
            # Run current pipeline
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
        
    def ppl_list(self):
        """List all pipelines"""
        self._ensure_initialized()
        self.pipeline_manager.list_pipelines()
        
    def ppl_print(self):
        """Print current pipeline configuration"""
        self._ensure_initialized()
        self.pipeline_manager.print_current_pipeline()
        
    def ppl_rm(self):
        """Remove package from current pipeline"""
        self._ensure_initialized()
        package_spec = self.kwargs['package_spec']
        self.pipeline_manager.remove_package(package_spec)
        
    def cd(self):
        """Change current pipeline"""
        self._ensure_initialized()
        pipeline_name = self.kwargs['pipeline_name']
        self.pipeline_manager.change_current_pipeline(pipeline_name)
        
    def repo_add(self):
        """Add repository"""
        self._ensure_initialized()
        repo_path = self.kwargs['repo_path']
        force = self.kwargs.get('force', False)
        self.repo_manager.add_repository(repo_path, force=force)
        
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
        
    def ppl_env_build(self):
        """Build environment for current pipeline"""
        self._ensure_initialized()
        self.env_manager.build_pipeline_environment(self.remainder)
        
    def ppl_env_copy(self):
        """Copy named environment to current pipeline"""
        self._ensure_initialized()
        env_name = self.kwargs['env_name']
        self.env_manager.copy_named_environment(env_name)
        
    def ppl_env_show(self):
        """Show current pipeline environment"""
        self._ensure_initialized()
        self.env_manager.show_pipeline_environment()
        
    def env_build(self):
        """Build a named environment"""
        self._ensure_initialized()
        env_name = self.kwargs['env_name']
        self.env_manager.build_named_environment(env_name, self.remainder)
        
    def env_list(self):
        """List all named environments"""
        self._ensure_initialized()
        envs = self.env_manager.list_named_environments()
        if envs:
            print("Available named environments:")
            for env_name in sorted(envs):
                print(f"  {env_name}")
        else:
            print("No named environments found. Create one with 'jarvis env build <name>'")
            
    def env_show(self):
        """Show a named environment"""
        self._ensure_initialized()
        env_name = self.kwargs['env_name']
        self.env_manager.show_named_environment(env_name)
        
    def hostfile_set(self):
        """Set hostfile"""
        self._ensure_initialized()
        hostfile_path = self.kwargs['hostfile_path']
        self.jarvis_config.set_hostfile(hostfile_path)
        
    def rg_build(self):
        """Build resource graph"""
        self._ensure_initialized()
        benchmark = not self.kwargs.get('no_benchmark', False)
        duration = self.kwargs.get('duration', 25)
        self.rg_manager.build_resource_graph(benchmark=benchmark, duration=duration)
        
    def rg_show(self):
        """Show resource graph summary"""
        self._ensure_initialized()
        self.rg_manager.show_resource_graph()
        
    def rg_nodes(self):
        """List nodes in resource graph"""
        self._ensure_initialized()
        self.rg_manager.list_nodes()
        
    def rg_node(self):
        """Show detailed node information"""
        self._ensure_initialized()
        hostname = self.kwargs['hostname']
        self.rg_manager.show_node_details(hostname)
        
    def rg_filter(self):
        """Filter storage by device type"""
        self._ensure_initialized()
        dev_type = self.kwargs['dev_type']
        self.rg_manager.filter_by_type(dev_type)
        
    def rg_load(self):
        """Load resource graph from file"""
        self._ensure_initialized()
        file_path = Path(self.kwargs['file_path'])
        self.rg_manager.load_resource_graph(file_path)
        
    def ppl_index_load(self):
        """Load a pipeline script from an index"""
        self._ensure_initialized()
        index_query = self.kwargs['index_query']
        self.pipeline_index_manager.load_pipeline_from_index(index_query)
        
    def ppl_index_copy(self):
        """Copy a pipeline script from an index"""
        self._ensure_initialized()
        index_query = self.kwargs['index_query']
        output = self.kwargs.get('output')
        self.pipeline_index_manager.copy_pipeline_from_index(index_query, output)
        
    def ppl_index_list(self):
        """List available pipeline scripts in indexes"""
        self._ensure_initialized()
        repo_name = self.kwargs.get('repo_name')
        available_scripts = self.pipeline_index_manager.list_available_scripts(repo_name)
        
        if not available_scripts:
            print("No pipeline indexes found in any repositories.")
            return
            
        if repo_name:
            print(f"Available pipeline scripts in {repo_name}:")
        else:
            print("Available pipeline scripts:")
            
        for repo, scripts in available_scripts.items():
            if repo_name and repo != repo_name:
                continue
            if not repo_name:
                print(f"  {repo}:")
            for script in scripts:
                if repo_name:
                    print(f"  {script}")
                else:
                    print(f"    {script}")


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
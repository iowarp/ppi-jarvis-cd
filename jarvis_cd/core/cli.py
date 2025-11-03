import sys
import os
from pathlib import Path
from jarvis_cd.util.argparse import ArgParse
from jarvis_cd.core.config import Jarvis
from jarvis_cd.core.pipeline import Pipeline
from jarvis_cd.core.pipeline_index import PipelineIndexManager
from jarvis_cd.core.repository import RepositoryManager
from jarvis_cd.core.pkg import Pkg
from jarvis_cd.core.environment import EnvironmentManager
from jarvis_cd.core.resource_graph import ResourceGraphManager


class JarvisCLI(ArgParse):
    """
    Main Jarvis CLI using the custom ArgParse class.
    Provides commands for initialization, pipeline management, repository management, etc.
    """
    
    def __init__(self):
        super().__init__()
        self.jarvis = None
        self.jarvis_config = None
        self.current_pipeline = None
        self.pipeline_index_manager = None
        self.repo_manager = None
        self.env_manager = None
        self.rg_manager = None
        self.module_manager = None
        
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
                'default': '~/.ppi-jarvis/config',
                'class': 'dirs',
                'rank': 0
            },
            {
                'name': 'private_dir',
                'msg': 'Private data directory',
                'type': str,
                'pos': True,
                'default': '~/.ppi-jarvis/private',
                'class': 'dirs',
                'rank': 1
            },
            {
                'name': 'shared_dir',
                'msg': 'Shared data directory',
                'type': str,
                'pos': True,
                'default': '~/.ppi-jarvis/shared',
                'class': 'dirs',
                'rank': 2
            },
            {
                'name': 'force',
                'msg': 'Force override of existing repos and resource_graph',
                'type': bool,
                'default': False,
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
            },
            {
                'name': 'container',
                'msg': 'Rebuild container image',
                'type': bool,
                'default': False
            },
            {
                'name': 'no_cache',
                'msg': 'Disable cache during container rebuild',
                'type': bool,
                'default': False
            }
        ])

        self.add_cmd('ppl conf', msg="Configure pipeline parameters")
        self.add_args([
            {
                'name': 'hostfile',
                'msg': 'Path to pipeline-specific hostfile',
                'type': str,
                'default': None,
            },
            {
                'name': 'container_build',
                'msg': 'Container build name (for building custom image)',
                'type': str,
                'default': None,
            },
            {
                'name': 'container_image',
                'msg': 'Pre-built container image to use',
                'type': str,
                'default': None,
            },
            {
                'name': 'container_engine',
                'msg': 'Container engine (docker/podman)',
                'type': str,
                'default': None,
            },
            {
                'name': 'container_base',
                'msg': 'Base container image',
                'type': str,
                'default': None,
            },
            {
                'name': 'container_ssh_port',
                'msg': 'SSH port for containers',
                'type': int,
                'default': None,
            }
        ])

        self.add_cmd('ppl list', msg="List all pipelines", aliases=['ppl ls'])
        self.add_args([])
        
        self.add_cmd('ppl print', msg="Print current pipeline configuration")
        self.add_args([])

        self.add_cmd('ppl path', msg="Print pipeline directory paths")
        self.add_args([
            {
                'name': 'shared',
                'msg': 'Print only shared directory',
                'type': bool,
                'default': False,
                'prefix': '+'
            },
            {
                'name': 'private',
                'msg': 'Print only private directory',
                'type': bool,
                'default': False,
                'prefix': '+'
            },
            {
                'name': 'config',
                'msg': 'Print only config directory',
                'type': bool,
                'default': False,
                'prefix': '+'
            }
        ])

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
        
        self.add_cmd('ppl destroy', msg="Destroy a pipeline")
        self.add_args([
            {
                'name': 'pipeline_name',
                'msg': 'Name of pipeline to destroy (optional, defaults to current)',
                'type': str,
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
                'name': 'repo_name',
                'msg': 'Name of repository to remove (not full path)',
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

        # Container commands
        self.add_menu('container', msg="Container image management commands")

        self.add_cmd('container list', msg="List all container images", aliases=['container ls'])
        self.add_args([])

        self.add_cmd('container remove', msg="Remove a container image", aliases=['container rm'])
        self.add_args([
            {
                'name': 'container_name',
                'msg': 'Name of container to remove',
                'type': str,
                'required': True,
                'pos': True
            }
        ])

        self.add_cmd('container update', msg="Force rebuild a container image")
        self.add_args([
            {
                'name': 'container_name',
                'msg': 'Name of container to rebuild',
                'type': str,
                'required': True,
                'pos': True
            },
            {
                'name': 'no_cache',
                'msg': 'Disable cache during rebuild',
                'type': bool,
                'default': False
            },
            {
                'name': 'engine',
                'msg': 'Container engine to use (docker or podman)',
                'type': str,
                'default': None,
                'choices': ['docker', 'podman']
            }
        ])

        # Package commands
        self.add_menu('pkg', msg="Package management commands")
        
        self.add_cmd('pkg configure', msg="Configure a package", aliases=['pkg conf'], keep_remainder=True)
        self.add_args([
            {
                'name': 'package_spec',
                'msg': 'Package to configure (pkg or pipeline.pkg)',
                'type': str,
                'required': True,
                'pos': True
            }
        ])
        
        self.add_cmd('pkg readme', msg="Show package README")
        self.add_args([
            {
                'name': 'package_spec',
                'msg': 'Package to show README for (pkg or repo.pkg)',
                'type': str,
                'required': True,
                'pos': True
            }
        ])
        
        self.add_cmd('pkg path', msg="Show package directory paths")
        self.add_args([
            {
                'name': 'package_spec',
                'msg': 'Package to show paths for (pkg or repo.pkg)',
                'type': str,
                'required': True,
                'pos': True
            },
            {
                'name': 'shared',
                'msg': 'Print only shared directory',
                'type': bool,
                'default': False,
                'prefix': '+'
            },
            {
                'name': 'private',
                'msg': 'Print only private directory',
                'type': bool,
                'default': False,
                'prefix': '+'
            },
            {
                'name': 'config',
                'msg': 'Print only config directory',
                'type': bool,
                'default': False,
                'prefix': '+'
            }
        ])

        self.add_cmd('pkg help', msg="Show package configuration help")
        self.add_args([
            {
                'name': 'package_spec',
                'msg': 'Package to show help for (pkg or repo.pkg)',
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
        
        self.add_cmd('rg path', msg="Show path to current resource graph file")
        self.add_args([])
        
        # Build commands
        self.add_menu('build', msg="Build environment profiles and configurations")
        
        self.add_cmd('build profile', msg="Build environment profile")
        self.add_args([
            {
                'name': 'm',
                'msg': 'Output method (dotenv, cmake, clion, vscode)',
                'type': str,
                'default': 'dotenv'
            },
            {
                'name': 'path',
                'msg': 'Output file path (prints to console if not specified)',
                'type': str,
                'required': False
            }
        ])
        
        # Module management commands
        self.add_menu('mod', msg="Module management commands")
        
        self.add_cmd('mod create', msg="Create a new module")
        self.add_args([
            {
                'name': 'mod_name',
                'msg': 'Module name',
                'type': str,
                'required': False,
                'pos': True
            }
        ])
        
        self.add_cmd('mod cd', msg="Set current module")
        self.add_args([
            {
                'name': 'mod_name',
                'msg': 'Module name',
                'type': str,
                'required': True,
                'pos': True
            }
        ])
        
        self.add_cmd('mod prepend', msg="Prepend environment variables to module", keep_remainder=True)
        self.add_args([
            {
                'name': 'mod_name',
                'msg': 'Module name (optional, uses current)',
                'type': str,
                'required': False,
                'pos': True
            }
        ])
        
        self.add_cmd('mod setenv', msg="Set environment variables in module", keep_remainder=True)
        self.add_args([
            {
                'name': 'mod_name',
                'msg': 'Module name (optional, uses current)',
                'type': str,
                'required': False,
                'pos': True
            }
        ])
        
        self.add_cmd('mod destroy', msg="Destroy a module")
        self.add_args([
            {
                'name': 'mod_name',
                'msg': 'Module name (optional, uses current)',
                'type': str,
                'required': False,
                'pos': True
            }
        ])

        self.add_cmd('mod clear', msg="Clear module directory except src/")
        self.add_args([
            {
                'name': 'mod_name',
                'msg': 'Module name (optional, uses current)',
                'type': str,
                'required': False,
                'pos': True
            }
        ])

        self.add_cmd('mod src', msg="Show module source directory")
        self.add_args([
            {
                'name': 'mod_name',
                'msg': 'Module name (optional, uses current)',
                'type': str,
                'required': False,
                'pos': True
            }
        ])
        
        self.add_cmd('mod root', msg="Show module root directory")
        self.add_args([
            {
                'name': 'mod_name',
                'msg': 'Module name (optional, uses current)',
                'type': str,
                'required': False,
                'pos': True
            }
        ])
        
        self.add_cmd('mod tcl', msg="Show module TCL file path")
        self.add_args([
            {
                'name': 'mod_name',
                'msg': 'Module name (optional, uses current)',
                'type': str,
                'required': False,
                'pos': True
            }
        ])
        
        self.add_cmd('mod yaml', msg="Show module YAML file path")
        self.add_args([
            {
                'name': 'mod_name',
                'msg': 'Module name (optional, uses current)',
                'type': str,
                'required': False,
                'pos': True
            }
        ])
        
        self.add_cmd('mod dir', msg="Show modules directory")
        self.add_args([])
        
        self.add_cmd('mod list', msg="List all modules")
        self.add_args([])
        
        self.add_cmd('mod profile', msg="Build environment profile", keep_remainder=True)
        self.add_args([])
        
        self.add_cmd('mod import', msg="Import module from command", keep_remainder=True)
        self.add_args([
            {
                'name': 'mod_name',
                'msg': 'Module name',
                'type': str,
                'required': True,
                'pos': True
            }
        ])
        
        self.add_cmd('mod update', msg="Update module using stored command")
        self.add_args([
            {
                'name': 'mod_name',
                'msg': 'Module name (optional, uses current)',
                'type': str,
                'required': False,
                'pos': True
            }
        ])
        
        self.add_cmd('mod build profile', msg="Build environment profile")
        self.add_args([
            {
                'name': 'm',
                'msg': 'Output method (dotenv, cmake, clion, vscode)',
                'type': str,
                'default': 'dotenv',
                'aliases': ['method']
            },
            {
                'name': 'path',
                'msg': 'Output file path (optional)',
                'type': str,
                'required': False
            }
        ])

        # Module dependency commands
        self.add_menu('mod dep', msg="Module dependency management")

        self.add_cmd('mod dep add', msg="Add a module dependency")
        self.add_args([
            {
                'name': 'dep_name',
                'msg': 'Dependency module name',
                'type': str,
                'required': True,
                'pos': True
            },
            {
                'name': 'mod_name',
                'msg': 'Module name (optional, uses current)',
                'type': str,
                'required': False,
                'pos': True
            }
        ])

        self.add_cmd('mod dep remove', msg="Remove a module dependency")
        self.add_args([
            {
                'name': 'dep_name',
                'msg': 'Dependency module name',
                'type': str,
                'required': True,
                'pos': True
            },
            {
                'name': 'mod_name',
                'msg': 'Module name (optional, uses current)',
                'type': str,
                'required': False,
                'pos': True
            }
        ])
        
    def _ensure_config_loaded(self):
        """Ensure Jarvis is loaded (doesn't require full initialization)"""
        if self.jarvis_config is None:
            self.jarvis_config = Jarvis.get_instance()

        # Initialize managers that don't require full Jarvis initialization
        if self.repo_manager is None:
            self.repo_manager = RepositoryManager(self.jarvis_config)

    def _ensure_initialized(self):
        """Ensure Jarvis is initialized before running commands"""
        if self.jarvis_config is None:
            self.jarvis_config = Jarvis.get_instance()

        if not self.jarvis_config.is_initialized():
            print("Error: Jarvis not initialized. Run 'jarvis init' first.")
            sys.exit(1)

        # Get Jarvis singleton instance (same as jarvis_config now)
        if self.jarvis is None:
            self.jarvis = self.jarvis_config
            
        # Initialize managers
        if self.repo_manager is None:
            self.repo_manager = RepositoryManager(self.jarvis_config)
        if self.env_manager is None:
            self.env_manager = EnvironmentManager(self.jarvis_config)
        if self.rg_manager is None:
            self.rg_manager = ResourceGraphManager()
        if self.pipeline_index_manager is None:
            self.pipeline_index_manager = PipelineIndexManager(self.jarvis_config)
        if self.module_manager is None:
            from jarvis_cd.core.module_manager import ModuleManager
            self.module_manager = ModuleManager(self.jarvis_config)
        
        # Load current pipeline if one exists
        current_pipeline_name = self.jarvis_config.get_current_pipeline()
        if current_pipeline_name:
            try:
                self.current_pipeline = Pipeline(current_pipeline_name)
            except Exception:
                # Pipeline may not exist or be corrupted, continue without it
                self.current_pipeline = None
    
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
        force = self.kwargs.get('force', False)

        jarvis = Jarvis.get_instance()
        jarvis.initialize(config_dir, private_dir, shared_dir, force=force)

        # Save jarvis instance to self so subsequent commands use the same instance
        self.jarvis_config = jarvis
        self.jarvis = jarvis

        print(f"Jarvis initialized successfully!")
        print(f"Config dir: {config_dir}")
        print(f"Private dir: {private_dir}")
        print(f"Shared dir: {shared_dir}")
        
    def ppl_create(self):
        """Create a new pipeline"""
        self._ensure_initialized()
        pipeline_name = self.kwargs['pipeline_name']
        
        # Create new pipeline
        pipeline = Pipeline()
        pipeline.create(pipeline_name)
        self.current_pipeline = pipeline
        
    def ppl_append(self):
        """Append package to current pipeline"""
        self._ensure_initialized()
        package_spec = self.kwargs['package_spec']
        package_alias = self.kwargs.get('package_alias')
        
        if not self.current_pipeline:
            # Try to load current pipeline
            current_name = self.jarvis_config.get_current_pipeline()
            if current_name:
                self.current_pipeline = Pipeline(current_name)
            else:
                raise ValueError("No current pipeline. Create one with 'jarvis ppl create <name>'")
        
        self.current_pipeline.append(package_spec, package_alias)
        
    def ppl_run(self):
        """Run pipeline"""
        self._ensure_initialized()
        load_type = self.kwargs.get('load_type', 'current')
        pipeline_file = self.kwargs.get('pipeline_file')
        
        if load_type == 'yaml':
            if not pipeline_file:
                raise ValueError("Pipeline file is required when load_type is 'yaml'")
            # Load and run pipeline file in one command
            pipeline = Pipeline()
            pipeline.run(load_type, pipeline_file)
            self.current_pipeline = pipeline
        else:
            # Run current pipeline
            if not self.current_pipeline:
                current_name = self.jarvis_config.get_current_pipeline()
                if current_name:
                    self.current_pipeline = Pipeline(current_name)
                else:
                    raise ValueError("No current pipeline to run")
            
            self.current_pipeline.run()
        
    def ppl_start(self):
        """Start current pipeline"""
        self._ensure_initialized()
        if not self.current_pipeline:
            current_name = self.jarvis_config.get_current_pipeline()
            if current_name:
                self.current_pipeline = Pipeline(current_name)
            else:
                raise ValueError("No current pipeline to start")
        
        self.current_pipeline.start()
        
    def ppl_stop(self):
        """Stop current pipeline"""
        self._ensure_initialized()
        if not self.current_pipeline:
            current_name = self.jarvis_config.get_current_pipeline()
            if current_name:
                self.current_pipeline = Pipeline(current_name)
            else:
                raise ValueError("No current pipeline to stop")
        
        self.current_pipeline.stop()
        
    def ppl_kill(self):
        """Kill current pipeline"""
        self._ensure_initialized()
        if not self.current_pipeline:
            current_name = self.jarvis_config.get_current_pipeline()
            if current_name:
                self.current_pipeline = Pipeline(current_name)
            else:
                raise ValueError("No current pipeline to kill")
        
        self.current_pipeline.kill()
        
    def ppl_clean(self):
        """Clean current pipeline"""
        self._ensure_initialized()
        if not self.current_pipeline:
            current_name = self.jarvis_config.get_current_pipeline()
            if current_name:
                self.current_pipeline = Pipeline(current_name)
            else:
                raise ValueError("No current pipeline to clean")
        
        self.current_pipeline.clean()
        
    def ppl_status(self):
        """Show pipeline status"""
        self._ensure_initialized()
        if not self.current_pipeline:
            current_name = self.jarvis_config.get_current_pipeline()
            if current_name:
                self.current_pipeline = Pipeline(current_name)
            else:
                print("No current pipeline")
                return
        
        status = self.current_pipeline.status()
        print(status)
        
    def ppl_load(self):
        """Load pipeline from file"""
        self._ensure_initialized()
        load_type = self.kwargs['load_type']
        pipeline_file = self.kwargs['pipeline_file']

        pipeline = Pipeline()
        pipeline.load(load_type, pipeline_file)
        pipeline.build_container_if_needed()
        pipeline.configure_all_packages()

        self.current_pipeline = pipeline
        
    def ppl_update(self):
        """Update pipeline from last loaded file"""
        self._ensure_initialized()

        if not self.current_pipeline:
            current_name = self.jarvis_config.get_current_pipeline()
            if current_name:
                self.current_pipeline = Pipeline(current_name)
            else:
                raise ValueError("No current pipeline to update")

        # Use Pipeline.update() method with container rebuild flags
        rebuild_container = self.kwargs.get('container', False)
        no_cache = self.kwargs.get('no_cache', False)
        self.current_pipeline.update(rebuild_container=rebuild_container, no_cache=no_cache)

    def ppl_conf(self):
        """Configure pipeline parameters"""
        self._ensure_initialized()

        if not self.current_pipeline:
            current_name = self.jarvis_config.get_current_pipeline()
            if current_name:
                self.current_pipeline = Pipeline(current_name)
            else:
                raise ValueError("No current pipeline to configure")

        # Check if any parameters were provided
        params_provided = False
        needs_rebuild = False

        # Update hostfile
        if self.kwargs.get('hostfile') is not None:
            from jarvis_cd.util.hostfile import Hostfile
            hostfile_path = self.kwargs['hostfile']
            self.current_pipeline.hostfile = Hostfile(path=hostfile_path)
            print(f"Set pipeline hostfile: {hostfile_path}")
            params_provided = True
            needs_rebuild = True

        # Update container_build
        if self.kwargs.get('container_build') is not None:
            self.current_pipeline.container_build = self.kwargs['container_build']
            print(f"Set container_build: {self.kwargs['container_build']}")
            params_provided = True
            needs_rebuild = True

        # Update container_image
        if self.kwargs.get('container_image') is not None:
            self.current_pipeline.container_image = self.kwargs['container_image']
            print(f"Set container_image: {self.kwargs['container_image']}")
            params_provided = True
            needs_rebuild = False  # Using pre-built image, no rebuild needed

        # Update container_engine
        if self.kwargs.get('container_engine') is not None:
            self.current_pipeline.container_engine = self.kwargs['container_engine']
            print(f"Set container_engine: {self.kwargs['container_engine']}")
            params_provided = True

        # Update container_base
        if self.kwargs.get('container_base') is not None:
            self.current_pipeline.container_base = self.kwargs['container_base']
            print(f"Set container_base: {self.kwargs['container_base']}")
            params_provided = True
            needs_rebuild = True

        # Update container_ssh_port
        if self.kwargs.get('container_ssh_port') is not None:
            self.current_pipeline.container_ssh_port = self.kwargs['container_ssh_port']
            print(f"Set container_ssh_port: {self.kwargs['container_ssh_port']}")
            params_provided = True

        if not params_provided:
            print("No parameters provided. Use -h to see available options.")
            return

        # Save pipeline
        self.current_pipeline.save()

        # Rebuild container if needed (only if container_build is set)
        if needs_rebuild and self.current_pipeline.container_build:
            print("\nRebuilding container with updated configuration...")
            self.current_pipeline.update(rebuild_container=True, no_cache=False)

    def ppl_list(self):
        """List all pipelines"""
        self._ensure_initialized()
        
        pipelines_dir = self.jarvis_config.get_pipelines_dir()
        
        if not pipelines_dir.exists():
            print("No pipelines directory found. Create a pipeline first with 'jarvis ppl create'.")
            return
            
        pipeline_dirs = [d for d in pipelines_dir.iterdir() if d.is_dir()]
        
        if not pipeline_dirs:
            print("No pipelines found. Create a pipeline first with 'jarvis ppl create'.")
            return
            
        current_pipeline_name = self.jarvis_config.get_current_pipeline()
        
        print("Available pipelines:")
        for pipeline_dir in sorted(pipeline_dirs):
            pipeline_name = pipeline_dir.name
            config_file = pipeline_dir / 'pipeline.yaml'
            
            if config_file.exists():
                try:
                    import yaml
                    with open(config_file, 'r') as f:
                        pipeline_config = yaml.safe_load(f) or {}
                    
                    num_packages = len(pipeline_config.get('packages', []))
                    marker = "* " if pipeline_name == current_pipeline_name else "  "
                    print(f"{marker}{pipeline_name} ({num_packages} packages)")
                    
                except Exception as e:
                    marker = "* " if pipeline_name == current_pipeline_name else "  "
                    print(f"{marker}{pipeline_name} (error reading config: {e})")
            else:
                marker = "* " if pipeline_name == current_pipeline_name else "  "
                print(f"{marker}{pipeline_name} (no config file)")
                
        if current_pipeline_name:
            print(f"\nCurrent pipeline: {current_pipeline_name}")
        else:
            print("\nNo current pipeline set. Use 'jarvis cd <pipeline>' to switch.")
        
    def ppl_print(self):
        """Print current pipeline configuration"""
        self._ensure_initialized()
        
        current_pipeline_name = self.jarvis_config.get_current_pipeline()
        
        if not current_pipeline_name:
            print("No current pipeline set. Use 'jarvis cd <pipeline>' to switch.")
            return
            
        if not self.current_pipeline:
            try:
                self.current_pipeline = Pipeline(current_pipeline_name)
            except Exception as e:
                print(f"Error loading current pipeline: {e}")
                return
        
        print(f"Pipeline: {self.current_pipeline.name}")
        print(f"Directory: {self.jarvis_config.get_pipeline_dir(current_pipeline_name)}")

        # Show hostfile configuration
        if hasattr(self.current_pipeline, 'hostfile') and self.current_pipeline.hostfile:
            print(f"Hostfile: {self.current_pipeline.hostfile.path or '(in-memory)'}")
            print(f"  Hosts: {', '.join(self.current_pipeline.hostfile.hosts)}")
        else:
            # Show that it falls back to jarvis global hostfile
            jarvis_hostfile = self.jarvis.hostfile
            print(f"Hostfile: (using global jarvis hostfile)")
            print(f"  Hosts: {', '.join(jarvis_hostfile.hosts)}")

        # Show container configuration if set
        if hasattr(self.current_pipeline, 'is_containerized') and self.current_pipeline.is_containerized():
            print(f"Container Configuration:")
            if self.current_pipeline.container_build:
                print(f"  Build Name: {self.current_pipeline.container_build}")
                print(f"  Base: {self.current_pipeline.container_base}")
            if self.current_pipeline.container_image:
                print(f"  Image: {self.current_pipeline.container_image}")
            print(f"  Engine: {self.current_pipeline.container_engine}")
            print(f"  SSH Port: {self.current_pipeline.container_ssh_port}")

        if self.current_pipeline.packages:
            print("Packages:")
            for pkg_def in self.current_pipeline.packages:
                pkg_id = pkg_def.get('pkg_id', 'unknown')
                pkg_type = pkg_def.get('pkg_type', 'unknown')
                global_id = pkg_def.get('global_id', pkg_id)
                config = pkg_def.get('config', {})
                
                print(f"  {pkg_id}:")
                print(f"    Type: {pkg_type}")
                print(f"    Global ID: {global_id}")
                
                if config:
                    print("    Configuration:")
                    for key, value in config.items():
                        print(f"      {key}: {value}")
                else:
                    print("    Configuration: None")
        else:
            print("No packages in pipeline")
        
        # Print interceptors if they exist
        if hasattr(self.current_pipeline, 'interceptors') and self.current_pipeline.interceptors:
            print("Interceptors:")
            for interceptor_name, interceptor_def in self.current_pipeline.interceptors.items():
                interceptor_type = interceptor_def.get('pkg_type', 'unknown')
                global_id = interceptor_def.get('global_id', interceptor_name)
                config = interceptor_def.get('config', {})
                
                print(f"  {interceptor_name}:")
                print(f"    Type: {interceptor_type}")
                print(f"    Global ID: {global_id}")
                
                if config:
                    print("    Configuration:")
                    for key, value in config.items():
                        print(f"      {key}: {value}")
                else:
                    print("    Configuration: None")
        else:
            print("No interceptors in pipeline")

        if hasattr(self.current_pipeline, 'last_loaded_file') and self.current_pipeline.last_loaded_file:
            print(f"Last loaded from: {self.current_pipeline.last_loaded_file}")

    def ppl_path(self):
        """Print pipeline directory paths"""
        self._ensure_initialized()

        current_pipeline_name = self.jarvis_config.get_current_pipeline()

        if not current_pipeline_name:
            print("No current pipeline set. Use 'jarvis cd <pipeline>' to switch.", file=sys.stderr)
            sys.exit(1)

        # Get directories
        config_dir = self.jarvis_config.get_pipeline_dir(current_pipeline_name)
        shared_dir = self.jarvis_config.get_pipeline_shared_dir(current_pipeline_name)
        private_dir = self.jarvis_config.get_pipeline_private_dir(current_pipeline_name)

        # Check which flags are set
        show_shared = self.kwargs.get('shared', False)
        show_private = self.kwargs.get('private', False)
        show_config = self.kwargs.get('config', False)

        # If no flags set, show all directories
        if not (show_shared or show_private or show_config):
            print(f"config:  {config_dir}")
            print(f"shared:  {shared_dir}")
            print(f"private: {private_dir}")
        else:
            # Show only requested directory (single line, no label)
            if show_config:
                print(config_dir)
            elif show_shared:
                print(shared_dir)
            elif show_private:
                print(private_dir)

    def ppl_rm(self):
        """Remove package from current pipeline"""
        self._ensure_initialized()
        package_spec = self.kwargs['package_spec']
        
        if not self.current_pipeline:
            current_name = self.jarvis_config.get_current_pipeline()
            if current_name:
                self.current_pipeline = Pipeline(current_name)
            else:
                raise ValueError("No current pipeline")
        
        self.current_pipeline.rm(package_spec)
        
    def ppl_destroy(self):
        """Destroy a pipeline"""
        self._ensure_initialized()
        pipeline_name = self.kwargs.get('pipeline_name')
        
        if pipeline_name:
            # Destroy specific pipeline
            pipeline = Pipeline()
            pipeline.destroy(pipeline_name)
        else:
            # Destroy current pipeline
            if not self.current_pipeline:
                current_name = self.jarvis_config.get_current_pipeline()
                if current_name:
                    self.current_pipeline = Pipeline(current_name)
                else:
                    print("No current pipeline to destroy. Specify a pipeline name.")
                    return
            
            self.current_pipeline.destroy()
            self.current_pipeline = None
        
    def cd(self):
        """Change current pipeline"""
        self._ensure_initialized()
        pipeline_name = self.kwargs['pipeline_name']
        
        pipeline_dir = self.jarvis_config.get_pipeline_dir(pipeline_name)
        
        if not pipeline_dir.exists():
            print(f"Pipeline '{pipeline_name}' not found.")
            self.ppl_list()
            return
            
        config_file = pipeline_dir / 'pipeline.yaml'
        if not config_file.exists():
            print(f"Pipeline '{pipeline_name}' exists but has no configuration file.")
            print("You may need to recreate this pipeline.")
            return
            
        # Set current pipeline in configuration
        self.jarvis_config.set_current_pipeline(pipeline_name)
        
        # Load the new current pipeline
        self.current_pipeline = Pipeline(pipeline_name)
        
        print(f"Switched to pipeline: {pipeline_name}")
        
        # Show basic info about the pipeline
        try:
            num_packages = len(self.current_pipeline.packages)
            print(f"Pipeline has {num_packages} packages")
        except Exception as e:
            print(f"Warning: Could not read pipeline configuration: {e}")
        
    def repo_add(self):
        """Add repository"""
        self._ensure_config_loaded()
        repo_path = self.kwargs['repo_path']
        force = self.kwargs.get('force', False)
        self.repo_manager.add_repository(repo_path, force=force)

    def repo_remove(self):
        """Remove repository by name"""
        self._ensure_config_loaded()
        repo_name = self.kwargs['repo_name']
        self.repo_manager.remove_repository_by_name(repo_name)

    def repo_list(self):
        """List repositories"""
        self._ensure_config_loaded()
        self.repo_manager.list_repositories()

    def repo_create(self):
        """Create new package in repository"""
        self._ensure_config_loaded()
        package_name = self.kwargs['package_name']
        package_type = self.kwargs['package_type']
        self.repo_manager.create_package(package_name, package_type)

    def container_list(self):
        """List all container images"""
        self._ensure_initialized()
        from jarvis_cd.core.container import ContainerManager
        container_manager = ContainerManager()
        container_manager.list_containers()

    def container_remove(self):
        """Remove a container image"""
        self._ensure_initialized()
        container_name = self.kwargs['container_name']
        from jarvis_cd.core.container import ContainerManager
        container_manager = ContainerManager()
        container_manager.remove_container(container_name)

    def container_update(self):
        """Force rebuild a container image"""
        self._ensure_initialized()
        container_name = self.kwargs['container_name']
        no_cache = self.kwargs.get('no_cache', False)
        engine = self.kwargs.get('engine')
        from pathlib import Path

        containers_dir = Path.home() / '.ppi-jarvis' / 'containers'
        dockerfile_path = containers_dir / f'{container_name}.Dockerfile'

        if not dockerfile_path.exists():
            print(f"Error: Container '{container_name}' not found")
            print(f"Expected Dockerfile at: {dockerfile_path}")
            sys.exit(1)

        # Determine container engine
        from jarvis_cd.shell import Exec, LocalExecInfo
        import shutil

        if engine:
            # Use specified engine
            use_engine = engine
        elif shutil.which('podman'):
            use_engine = 'podman'
        else:
            use_engine = 'docker'

        # Build command with optional --no-cache flag
        no_cache_flag = " --no-cache" if no_cache else ""
        build_cmd = f"{use_engine} build{no_cache_flag} -t {container_name} -f {dockerfile_path} {containers_dir}"

        cache_msg = " (no cache)" if no_cache else " (with cache)"
        print(f"Rebuilding container image: {container_name}{cache_msg} using {use_engine}")
        Exec(build_cmd, LocalExecInfo()).run()
        print(f"Container image rebuilt: {container_name}")

    def pkg_configure(self):
        """Configure package"""
        self._ensure_initialized()
        package_spec = self.kwargs['package_spec']

        # Parse package specification
        if '.' in package_spec:
            # pipeline.pkg format
            pipeline_name, pkg_id = package_spec.split('.', 1)
            pipeline = Pipeline(pipeline_name)
            pipeline.configure_package(pkg_id, self.remainder)
        else:
            # Just package name - assume current pipeline
            if not self.current_pipeline:
                current_name = self.jarvis_config.get_current_pipeline()
                if current_name:
                    self.current_pipeline = Pipeline(current_name)
                else:
                    raise ValueError("No current pipeline. Specify as pipeline.pkg or create a pipeline first.")

            self.current_pipeline.configure_package(package_spec, self.remainder)
        
    def pkg_readme(self):
        """Show package README"""
        self._ensure_initialized()
        package_spec = self.kwargs['package_spec']
        
        # Parse package specification
        if '.' in package_spec:
            # Check if it's a pipeline.pkg or repo.pkg format
            parts = package_spec.split('.')
            if len(parts) == 2:
                # Could be either pipeline.pkg or repo.pkg
                # Try to determine based on whether it's an existing pipeline
                potential_pipeline = parts[0]
                pipeline_dir = self.jarvis_config.get_pipeline_dir(potential_pipeline)
                
                if pipeline_dir.exists():
                    # It's a pipeline.pkg format
                    pipeline_name, pkg_id = parts
                    pipeline = Pipeline(pipeline_name)
                    pipeline.show_package_readme(pkg_id)
                else:
                    # It's a repo.pkg format - load standalone
                    from jarvis_cd.core.pkg import Pkg
                    pkg_instance = Pkg.load_standalone(package_spec)
                    pkg_instance.show_readme()
            else:
                # It's a repo.pkg format - load standalone
                from jarvis_cd.core.pkg import Pkg
                pkg_instance = Pkg.load_standalone(package_spec)
                pkg_instance.show_readme()
        else:
            # Just package name - could be in current pipeline or standalone
            if self.current_pipeline or self.jarvis_config.get_current_pipeline():
                # Try pipeline first
                if not self.current_pipeline:
                    current_name = self.jarvis_config.get_current_pipeline()
                    self.current_pipeline = Pipeline(current_name)
                
                try:
                    self.current_pipeline.show_package_readme(package_spec)
                except ValueError:
                    # Package not in pipeline, try standalone
                    from jarvis_cd.core.pkg import Pkg
                    pkg_instance = Pkg.load_standalone(package_spec)
                    pkg_instance.show_readme()
            else:
                # No pipeline, load standalone
                from jarvis_cd.core.pkg import Pkg
                pkg_instance = Pkg.load_standalone(package_spec)
                pkg_instance.show_readme()
        
    def pkg_path(self):
        """Show package directory paths"""
        self._ensure_initialized()
        package_spec = self.kwargs['package_spec']

        # Get the requested paths
        path_flags = {
            'shared': self.kwargs.get('shared', False),
            'private': self.kwargs.get('private', False),
            'config': self.kwargs.get('config', False)
        }

        # Parse package specification
        if '.' in package_spec:
            # Check if it's a pipeline.pkg or repo.pkg format
            parts = package_spec.split('.')
            if len(parts) == 2:
                # Could be either pipeline.pkg or repo.pkg
                # Try to determine based on whether it's an existing pipeline
                potential_pipeline = parts[0]
                pipeline_dir = self.jarvis_config.get_pipeline_dir(potential_pipeline)

                if pipeline_dir.exists():
                    # It's a pipeline.pkg format
                    pipeline_name, pkg_id = parts
                    pipeline = Pipeline(pipeline_name)
                    pipeline.show_package_paths(pkg_id, path_flags)
                else:
                    # It's a repo.pkg format - load standalone
                    from jarvis_cd.core.pkg import Pkg
                    pkg_instance = Pkg.load_standalone(package_spec)
                    pkg_instance.show_paths(path_flags)
            else:
                # It's a repo.pkg format - load standalone
                from jarvis_cd.core.pkg import Pkg
                pkg_instance = Pkg.load_standalone(package_spec)
                pkg_instance.show_paths(path_flags)
        else:
            # Just package name - could be in current pipeline or standalone
            if self.current_pipeline or self.jarvis_config.get_current_pipeline():
                # Try pipeline first
                if not self.current_pipeline:
                    current_name = self.jarvis_config.get_current_pipeline()
                    self.current_pipeline = Pipeline(current_name)

                try:
                    self.current_pipeline.show_package_paths(package_spec, path_flags)
                except ValueError:
                    # Package not in pipeline, try standalone
                    from jarvis_cd.core.pkg import Pkg
                    pkg_instance = Pkg.load_standalone(package_spec)
                    pkg_instance.show_paths(path_flags)
            else:
                # No pipeline, load standalone
                from jarvis_cd.core.pkg import Pkg
                pkg_instance = Pkg.load_standalone(package_spec)
                pkg_instance.show_paths(path_flags)

    def pkg_help(self):
        """Show package configuration help"""
        self._ensure_initialized()
        package_spec = self.kwargs['package_spec']

        # Load the package standalone (repo.pkg format like builtin.ior)
        from jarvis_cd.core.pkg import Pkg
        pkg_instance = Pkg.load_standalone(package_spec)

        # Get the argparse instance and print help
        argparse = pkg_instance.get_argparse()
        argparse.print_help()

    def ppl_env_build(self):
        """Build environment for current pipeline and reconfigure packages"""
        self._ensure_initialized()
        self.env_manager.build_pipeline_environment(self.remainder)

        # Reconfigure packages with new environment
        if not self.current_pipeline:
            current_name = self.jarvis_config.get_current_pipeline()
            if current_name:
                self.current_pipeline = Pipeline(current_name)

        if self.current_pipeline:
            # Reload environment from env.yaml (don't reload full pipeline to avoid inline dict error)
            from pathlib import Path
            import yaml
            pipeline_dir = self.jarvis_config.get_pipeline_dir(self.current_pipeline.name)
            env_file = pipeline_dir / 'env.yaml'
            if env_file.exists():
                with open(env_file, 'r') as f:
                    self.current_pipeline.env = yaml.safe_load(f)

            # Reconfigure all packages with the new environment
            self.current_pipeline.build_container_if_needed()
            self.current_pipeline.configure_all_packages()
            print("Pipeline reconfigured with new environment")
        
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
        self.rg_manager.build(benchmark=benchmark, duration=duration)
        
    def build_profile(self):
        """Build environment profile"""
        self._ensure_initialized()
        method = self.kwargs.get('m', 'dotenv')
        path = self.kwargs.get('path')
        self.module_manager.build_profile(path, method)
        
    def rg_show(self):
        """Show resource graph summary"""
        self._ensure_initialized()
        self.rg_manager.show()
        
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
        self.rg_manager.load(file_path)
        
    def rg_path(self):
        """Show path to current resource graph file"""
        self._ensure_initialized()
        self.rg_manager.show_path()
        
    # Module management commands
    def mod_create(self):
        """Create a new module"""
        self._ensure_initialized()
        mod_name = self.kwargs.get('mod_name')
        if not mod_name:
            # Generate a unique module name or prompt user
            import time
            mod_name = f"module_{int(time.time())}"
            print(f"No module name provided, using: {mod_name}")
        self.module_manager.create_module(mod_name)
        
    def mod_cd(self):
        """Set current module"""
        self._ensure_initialized()
        mod_name = self.kwargs['mod_name']
        self.module_manager.set_current_module(mod_name)
        
    def mod_prepend(self):
        """Prepend environment variables to module"""
        self._ensure_initialized()
        mod_name = self.kwargs.get('mod_name')
        self.module_manager.prepend_env_vars(mod_name, self.remainder)
        
    def mod_setenv(self):
        """Set environment variables in module"""
        self._ensure_initialized()
        mod_name = self.kwargs.get('mod_name')
        self.module_manager.set_env_vars(mod_name, self.remainder)
        
    def mod_destroy(self):
        """Destroy a module"""
        self._ensure_initialized()
        mod_name = self.kwargs.get('mod_name')
        self.module_manager.destroy_module(mod_name)

    def mod_clear(self):
        """Clear module directory except src/"""
        self._ensure_initialized()
        mod_name = self.kwargs.get('mod_name')
        self.module_manager.clear_module(mod_name)

    def mod_src(self):
        """Show module source directory"""
        self._ensure_initialized()
        mod_name = self.kwargs.get('mod_name')
        print(self.module_manager.get_module_src_dir(mod_name))
        
    def mod_root(self):
        """Show module root directory"""
        self._ensure_initialized()
        mod_name = self.kwargs.get('mod_name')
        print(self.module_manager.get_module_root_dir(mod_name))
        
    def mod_tcl(self):
        """Show module TCL file path"""
        self._ensure_initialized()
        mod_name = self.kwargs.get('mod_name')
        print(self.module_manager.get_module_tcl_path(mod_name))
        
    def mod_yaml(self):
        """Show module YAML file path"""
        self._ensure_initialized()
        mod_name = self.kwargs.get('mod_name')
        print(self.module_manager.get_module_yaml_path(mod_name))
        
    def mod_dir(self):
        """Show modules directory"""
        self._ensure_initialized()
        print(self.module_manager.modules_dir)
        
    def mod_list(self):
        """List all modules"""
        self._ensure_initialized()
        self.module_manager.list_modules()
        
    def mod_profile(self):
        """Build environment profile"""
        self._ensure_initialized()
        # Parse remainder arguments for m= and path= format
        method = 'dotenv'  # default
        path = None
        
        if hasattr(self, 'remainder') and self.remainder:
            for arg in self.remainder:
                if arg.startswith('m='):
                    method = arg[2:]
                elif arg.startswith('path='):
                    path = arg[5:]
        
        self.module_manager.build_profile_new(path, method)
        
    def mod_import(self):
        """Import module from command"""
        self._ensure_initialized()
        mod_name = self.kwargs.get('mod_name')
        
        if not hasattr(self, 'remainder') or not self.remainder:
            raise ValueError("No command provided. Usage: jarvis mod import <mod_name> <command>")
        
        # Join remainder as the command to execute
        command = ' '.join(self.remainder)
        self.module_manager.import_module(mod_name, command)
        
    def mod_update(self):
        """Update module using stored command"""
        self._ensure_initialized()
        mod_name = self.kwargs.get('mod_name')
        self.module_manager.update_module(mod_name)
        
    def mod_build_profile(self):
        """Build environment profile"""
        self._ensure_initialized()
        method = self.kwargs.get('m', 'dotenv')
        path = self.kwargs.get('path')
        self.module_manager.build_profile(path, method)

    def mod_dep_add(self):
        """Add a module dependency"""
        self._ensure_initialized()
        dep_name = self.kwargs['dep_name']
        mod_name = self.kwargs.get('mod_name')
        self.module_manager.add_dependency(mod_name, dep_name)

    def mod_dep_remove(self):
        """Remove a module dependency"""
        self._ensure_initialized()
        dep_name = self.kwargs['dep_name']
        mod_name = self.kwargs.get('mod_name')
        self.module_manager.remove_dependency(mod_name, dep_name)

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
        from jarvis_cd.util.logger import logger, Color
        
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
            
        for repo, entries in available_scripts.items():
            if repo_name and repo != repo_name:
                continue
            if not repo_name:
                print(f"  {repo}:")
            for entry in entries:
                indent = "  " if repo_name else "    "
                if entry['type'] == 'file':
                    # Print files in default color
                    print(f"{indent}{entry['name']}")
                elif entry['type'] == 'directory':
                    # Print directories in cyan color with (directory) label
                    logger.print(Color.CYAN, f"{indent}{entry['name']} (directory)")


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
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from jarvis_cd.core.config import JarvisConfig, load_class, Jarvis


class PipelineManager:
    """
    Manages Jarvis pipelines - creation, loading, running, and lifecycle management.
    """
    
    def __init__(self, jarvis_config: JarvisConfig):
        """
        Initialize pipeline manager.
        
        :param jarvis_config: Jarvis configuration manager
        """
        self.jarvis_config = jarvis_config
        self.current_pipeline = None
        
    def create_pipeline(self, pipeline_name: str):
        """
        Create a new pipeline.
        
        :param pipeline_name: Name of the pipeline to create
        """
        pipeline_dir = self.jarvis_config.get_pipeline_dir(pipeline_name)
        pipeline_dir.mkdir(parents=True, exist_ok=True)
        
        # Create pipeline configuration
        pipeline_config = {
            'name': pipeline_name,
            'packages': [],
            'env': {},
            'created_at': str(Path().cwd()),
            'last_loaded_file': None
        }
        
        # Save pipeline configuration
        config_file = pipeline_dir / 'pipeline.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(pipeline_config, f, default_flow_style=False)
            
        # Create environment file
        env_file = pipeline_dir / 'env.yaml'
        with open(env_file, 'w') as f:
            yaml.dump({}, f, default_flow_style=False)
            
        # Set as current pipeline
        self.jarvis_config.set_current_pipeline(pipeline_name)
        
        print(f"Created pipeline: {pipeline_name}")
        print(f"Pipeline directory: {pipeline_dir}")
        
    def append_package(self, package_spec: str, package_alias: Optional[str] = None):
        """
        Append a package to the current pipeline.
        
        :param package_spec: Package specification (repo.pkg or just pkg)
        :param package_alias: Optional alias for the package
        """
        current_pipeline_dir = self.jarvis_config.get_current_pipeline_dir()
        if not current_pipeline_dir:
            raise ValueError("No current pipeline. Create one with 'jarvis ppl create <name>'")
            
        # Parse package specification
        if '.' in package_spec:
            repo_name, pkg_name = package_spec.split('.', 1)
        else:
            # Try to find package in available repos
            pkg_name = package_spec
            full_spec = self.jarvis_config.find_package(pkg_name)
            if not full_spec:
                raise ValueError(f"Package not found: {pkg_name}")
            package_spec = full_spec
            
        # Load pipeline configuration
        config_file = current_pipeline_dir / 'pipeline.yaml'
        with open(config_file, 'r') as f:
            pipeline_config = yaml.safe_load(f)
            
        # Determine package ID
        if package_alias:
            pkg_id = package_alias
        else:
            pkg_id = pkg_name
            
        # Check for duplicate package IDs
        existing_ids = [pkg['pkg_id'] for pkg in pipeline_config['packages']]
        if pkg_id in existing_ids:
            raise ValueError(f"Package ID already exists in pipeline: {pkg_id}")
            
        # Get default configuration from package
        default_config = self._get_package_default_config(package_spec)
        
        # Add package to pipeline
        package_entry = {
            'pkg_type': package_spec,
            'pkg_id': pkg_id,
            'pkg_name': pkg_name,
            'global_id': f"{pipeline_config['name']}.{pkg_id}",
            'config': default_config
        }
        
        pipeline_config['packages'].append(package_entry)
        
        # Save updated configuration
        with open(config_file, 'w') as f:
            yaml.dump(pipeline_config, f, default_flow_style=False)
            
        print(f"Added package {package_spec} as {pkg_id} to pipeline")
        
        # Display the package configuration
        if default_config:
            print("Package configured with default values:")
            self._print_package_config(package_entry, "  ")
        else:
            print("Package has no configurable options")
            
    def remove_package(self, package_spec: str):
        """
        Remove a package from a pipeline.
        
        :param package_spec: Package specification to remove (pkg_id or pipeline.pkg_id)
        """
        # Determine target pipeline and package
        if '.' in package_spec:
            # Full specification like "hermes.ior" - use specified pipeline
            target_pipeline_name, target_pkg_id = package_spec.split('.', 1)
            pipeline_dir = self.jarvis_config.get_pipeline_dir(target_pipeline_name)
            
            if not pipeline_dir.exists():
                raise ValueError(f"Pipeline not found: {target_pipeline_name}")
        else:
            # Just package ID like "ior" - use current pipeline
            target_pkg_id = package_spec
            pipeline_dir = self.jarvis_config.get_current_pipeline_dir()
            
            if not pipeline_dir:
                raise ValueError("No current pipeline. Create one with 'jarvis ppl create <name>' or specify as pipeline.package")
                
            # Get pipeline name for display
            config_file = pipeline_dir / 'pipeline.yaml'
            with open(config_file, 'r') as f:
                temp_config = yaml.safe_load(f)
                target_pipeline_name = temp_config['name']
            
        # Load pipeline configuration
        config_file = pipeline_dir / 'pipeline.yaml'
        with open(config_file, 'r') as f:
            pipeline_config = yaml.safe_load(f)
            
        # Find and remove the package
        packages = pipeline_config['packages']
        package_found = False
        
        for i, pkg_def in enumerate(packages):
            if pkg_def['pkg_id'] == target_pkg_id:
                removed_package = packages.pop(i)
                package_found = True
                break
                
        if not package_found:
            # List available packages to help the user
            available_ids = [pkg['pkg_id'] for pkg in packages]
            if available_ids:
                print(f"Package '{target_pkg_id}' not found in current pipeline.")
                print(f"Available packages: {', '.join(available_ids)}")
            else:
                print("No packages in current pipeline.")
            return
            
        # Save updated configuration
        with open(config_file, 'w') as f:
            yaml.dump(pipeline_config, f, default_flow_style=False)
            
        print(f"Removed package '{removed_package['pkg_id']}' ({removed_package['pkg_type']}) from pipeline '{target_pipeline_name}'")
        
    def load_pipeline(self, load_type: str, pipeline_file: str):
        """
        Load a pipeline from a file.
        
        :param load_type: Type of pipeline file (e.g., 'yaml')
        :param pipeline_file: Path to pipeline file
        """
        if load_type != 'yaml':
            raise ValueError(f"Unsupported pipeline file type: {load_type}")
            
        pipeline_file = Path(pipeline_file)
        if not pipeline_file.exists():
            raise FileNotFoundError(f"Pipeline file not found: {pipeline_file}")
            
        # Load pipeline definition
        with open(pipeline_file, 'r') as f:
            pipeline_def = yaml.safe_load(f)
            
        pipeline_name = pipeline_def.get('name', pipeline_file.stem)
        
        # Create or update pipeline
        pipeline_dir = self.jarvis_config.get_pipeline_dir(pipeline_name)
        pipeline_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert pipeline definition to internal format
        pipeline_config = {
            'name': pipeline_name,
            'packages': [],
            'env': pipeline_def.get('env', {}),
            'created_at': str(Path().cwd()),
            'last_loaded_file': str(pipeline_file.absolute())
        }
        
        # Process packages
        for pkg_def in pipeline_def.get('pkgs', []):
            pkg_type = pkg_def['pkg_type']
            pkg_id = pkg_def.get('pkg_name', pkg_type)
            
            package_entry = {
                'pkg_type': pkg_type,
                'pkg_id': pkg_id,
                'pkg_name': pkg_type.split('.')[-1],
                'global_id': f"{pipeline_name}.{pkg_id}",
                'config': {k: v for k, v in pkg_def.items() 
                          if k not in ['pkg_type', 'pkg_name', 'interceptors']},
                'interceptors': pkg_def.get('interceptors', [])
            }
            
            pipeline_config['packages'].append(package_entry)
            
        # Process interceptors
        for interceptor_def in pipeline_def.get('interceptors', []):
            pkg_type = interceptor_def['pkg_type']
            pkg_id = interceptor_def.get('pkg_name', pkg_type)
            
            package_entry = {
                'pkg_type': pkg_type,
                'pkg_id': pkg_id,
                'pkg_name': pkg_type.split('.')[-1],
                'global_id': f"{pipeline_name}.{pkg_id}",
                'config': {k: v for k, v in interceptor_def.items() 
                          if k not in ['pkg_type', 'pkg_name']},
                'is_interceptor': True
            }
            
            pipeline_config['packages'].append(package_entry)
            
        # Save pipeline configuration
        config_file = pipeline_dir / 'pipeline.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(pipeline_config, f, default_flow_style=False)
            
        # Save environment
        env_file = pipeline_dir / 'env.yaml'
        with open(env_file, 'w') as f:
            yaml.dump(pipeline_config['env'], f, default_flow_style=False)
            
        # Set as current pipeline
        self.jarvis_config.set_current_pipeline(pipeline_name)
        
        print(f"Loaded pipeline: {pipeline_name}")
        print(f"Packages: {[pkg['pkg_id'] for pkg in pipeline_config['packages']]}")
        
    def update_pipeline(self, update_type: str = 'yaml'):
        """
        Update current pipeline from last loaded file.
        
        :param update_type: Type of update (yaml)
        """
        current_pipeline_dir = self.jarvis_config.get_current_pipeline_dir()
        if not current_pipeline_dir:
            raise ValueError("No current pipeline")
            
        # Load pipeline configuration to get last loaded file
        config_file = current_pipeline_dir / 'pipeline.yaml'
        with open(config_file, 'r') as f:
            pipeline_config = yaml.safe_load(f)
            
        last_loaded_file = pipeline_config.get('last_loaded_file')
        if not last_loaded_file:
            raise ValueError("No pipeline file to update from")
            
        print(f"Updating pipeline from: {last_loaded_file}")
        self.load_pipeline(update_type, last_loaded_file)
        
    def run_pipeline(self):
        """Run the current pipeline (start all packages, then stop them)"""
        try:
            self.start_pipeline()
            print("Pipeline started successfully. Stopping packages...")
            self.stop_pipeline()
        except Exception as e:
            print(f"Error during pipeline run: {e}")
            print("Attempting to stop packages...")
            try:
                self.stop_pipeline()
            except Exception as stop_error:
                print(f"Error during cleanup: {stop_error}")
        
    def start_pipeline(self):
        """Start all packages in the current pipeline"""
        current_pipeline_dir = self.jarvis_config.get_current_pipeline_dir()
        if not current_pipeline_dir:
            raise ValueError("No current pipeline")
            
        # Load pipeline configuration
        config_file = current_pipeline_dir / 'pipeline.yaml'
        with open(config_file, 'r') as f:
            pipeline_config = yaml.safe_load(f)
            
        print(f"Starting pipeline: {pipeline_config['name']}")
        
        # Load and start each package
        for pkg_def in pipeline_config['packages']:
            try:
                print(f"Starting package: {pkg_def['pkg_id']}")
                pkg_instance = self._load_package_instance(pkg_def)
                
                if hasattr(pkg_instance, 'start'):
                    pkg_instance.start()
                else:
                    print(f"Package {pkg_def['pkg_id']} has no start method")
                    
            except Exception as e:
                print(f"Error starting package {pkg_def['pkg_id']}: {e}")
                
    def stop_pipeline(self):
        """Stop all packages in the current pipeline"""
        current_pipeline_dir = self.jarvis_config.get_current_pipeline_dir()
        if not current_pipeline_dir:
            raise ValueError("No current pipeline")
            
        # Load pipeline configuration
        config_file = current_pipeline_dir / 'pipeline.yaml'
        with open(config_file, 'r') as f:
            pipeline_config = yaml.safe_load(f)
            
        print(f"Stopping pipeline: {pipeline_config['name']}")
        
        # Stop each package in reverse order
        for pkg_def in reversed(pipeline_config['packages']):
            try:
                print(f"Stopping package: {pkg_def['pkg_id']}")
                pkg_instance = self._load_package_instance(pkg_def)
                
                if hasattr(pkg_instance, 'stop'):
                    pkg_instance.stop()
                else:
                    print(f"Package {pkg_def['pkg_id']} has no stop method")
                    
            except Exception as e:
                print(f"Error stopping package {pkg_def['pkg_id']}: {e}")
                
    def kill_pipeline(self):
        """Force kill all packages in the current pipeline"""
        current_pipeline_dir = self.jarvis_config.get_current_pipeline_dir()
        if not current_pipeline_dir:
            raise ValueError("No current pipeline")
            
        # Load pipeline configuration
        config_file = current_pipeline_dir / 'pipeline.yaml'
        with open(config_file, 'r') as f:
            pipeline_config = yaml.safe_load(f)
            
        print(f"Killing pipeline: {pipeline_config['name']}")
        
        # Kill each package
        for pkg_def in pipeline_config['packages']:
            try:
                print(f"Killing package: {pkg_def['pkg_id']}")
                pkg_instance = self._load_package_instance(pkg_def)
                
                if hasattr(pkg_instance, 'kill'):
                    pkg_instance.kill()
                else:
                    print(f"Package {pkg_def['pkg_id']} has no kill method")
                    
            except Exception as e:
                print(f"Error killing package {pkg_def['pkg_id']}: {e}")
                
    def clean_pipeline(self):
        """Clean all data for packages in the current pipeline"""
        current_pipeline_dir = self.jarvis_config.get_current_pipeline_dir()
        if not current_pipeline_dir:
            raise ValueError("No current pipeline")
            
        # Load pipeline configuration
        config_file = current_pipeline_dir / 'pipeline.yaml'
        with open(config_file, 'r') as f:
            pipeline_config = yaml.safe_load(f)
            
        print(f"Cleaning pipeline: {pipeline_config['name']}")
        
        # Clean each package
        for pkg_def in pipeline_config['packages']:
            try:
                print(f"Cleaning package: {pkg_def['pkg_id']}")
                pkg_instance = self._load_package_instance(pkg_def)
                
                if hasattr(pkg_instance, 'clean'):
                    pkg_instance.clean()
                else:
                    print(f"Package {pkg_def['pkg_id']} has no clean method")
                    
            except Exception as e:
                print(f"Error cleaning package {pkg_def['pkg_id']}: {e}")
                
    def show_status(self):
        """Show status of the current pipeline"""
        current_pipeline_dir = self.jarvis_config.get_current_pipeline_dir()
        if not current_pipeline_dir:
            print("No current pipeline")
            return
            
        # Load pipeline configuration
        config_file = current_pipeline_dir / 'pipeline.yaml'
        with open(config_file, 'r') as f:
            pipeline_config = yaml.safe_load(f)
            
        print(f"Pipeline: {pipeline_config['name']}")
        print(f"Directory: {current_pipeline_dir}")
        print("Packages:")
        
        for pkg_def in pipeline_config['packages']:
            try:
                pkg_instance = self._load_package_instance(pkg_def)
                
                if hasattr(pkg_instance, 'status'):
                    status = pkg_instance.status()
                    print(f"  {pkg_def['pkg_id']}: {status}")
                else:
                    print(f"  {pkg_def['pkg_id']}: no status method")
                    
            except Exception as e:
                print(f"  {pkg_def['pkg_id']}: error ({e})")
                
    def _load_package_instance(self, pkg_def: Dict[str, Any]):
        """
        Load a package instance from package definition.
        
        :param pkg_def: Package definition dictionary
        :return: Package instance
        """
        pkg_type = pkg_def['pkg_type']
        
        # Find package class
        if '.' in pkg_type:
            # Full specification like "builtin.ior"
            import_parts = pkg_type.split('.')
            repo_name = import_parts[0]
            pkg_name = import_parts[1]
        else:
            # Just package name, search in repos
            full_spec = self.jarvis_config.find_package(pkg_type)
            if not full_spec:
                raise ValueError(f"Package not found: {pkg_type}")
            import_parts = full_spec.split('.')
            repo_name = import_parts[0]
            pkg_name = import_parts[1]
            
        # Determine class name (capitalize first letter)
        class_name = pkg_name.capitalize()
        
        # Load class
        if repo_name == 'builtin':
            repo_path = str(self.jarvis_config.get_builtin_repo_path())
        else:
            # Find repo path in registered repos
            repo_path = None
            for registered_repo in self.jarvis_config.repos['repos']:
                if Path(registered_repo).name == repo_name:
                    repo_path = registered_repo
                    break
                    
            if not repo_path:
                raise ValueError(f"Repository not found: {repo_name}")
                
        import_str = f"{repo_name}.{pkg_name}.package"
        pkg_class = load_class(import_str, repo_path, class_name)
        
        if not pkg_class:
            raise ValueError(f"Package class not found: {class_name} in {import_str}")
            
        # Create instance
        pkg_instance = pkg_class()
        
        # Set basic attributes if they exist
        if hasattr(pkg_instance, 'pkg_id'):
            pkg_instance.pkg_id = pkg_def['pkg_id']
        if hasattr(pkg_instance, 'global_id'):
            pkg_instance.global_id = pkg_def['global_id']
        if hasattr(pkg_instance, 'config'):
            base_config = pkg_def.get('config', {})
            
            # Ensure common parameters are present
            base_config.setdefault('do_dbg', False)
            base_config.setdefault('dbg_port', 50000)
            
            pkg_instance.config = base_config
            
        # Set jarvis singleton for package access
        if hasattr(pkg_instance, 'jarvis'):
            pkg_instance.jarvis = Jarvis.get_instance()
            
        return pkg_instance
        
    def list_pipelines(self):
        """List all available pipelines"""
        pipelines_dir = self.jarvis_config.get_pipelines_dir()
        
        if not pipelines_dir.exists():
            print("No pipelines directory found. Create a pipeline first with 'jarvis ppl create'.")
            return
            
        pipeline_dirs = [d for d in pipelines_dir.iterdir() if d.is_dir()]
        
        if not pipeline_dirs:
            print("No pipelines found. Create a pipeline first with 'jarvis ppl create'.")
            return
            
        current_pipeline = self.jarvis_config.get_current_pipeline()
        
        print("Available pipelines:")
        for pipeline_dir in sorted(pipeline_dirs):
            pipeline_name = pipeline_dir.name
            config_file = pipeline_dir / 'pipeline.yaml'
            
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        pipeline_config = yaml.safe_load(f) or {}
                    
                    num_packages = len(pipeline_config.get('packages', []))
                    marker = "* " if pipeline_name == current_pipeline else "  "
                    print(f"{marker}{pipeline_name} ({num_packages} packages)")
                    
                except Exception as e:
                    marker = "* " if pipeline_name == current_pipeline else "  "
                    print(f"{marker}{pipeline_name} (error reading config: {e})")
            else:
                marker = "* " if pipeline_name == current_pipeline else "  "
                print(f"{marker}{pipeline_name} (no config file)")
                
        if current_pipeline:
            print(f"\nCurrent pipeline: {current_pipeline}")
        else:
            print("\nNo current pipeline set. Use 'jarvis cd <pipeline>' to switch.")
            
    def print_current_pipeline(self):
        """Print the current pipeline configuration"""
        current_pipeline = self.jarvis_config.get_current_pipeline()
        
        if not current_pipeline:
            print("No current pipeline set. Use 'jarvis cd <pipeline>' to switch.")
            return
            
        pipeline_dir = self.jarvis_config.get_pipeline_dir(current_pipeline)
        config_file = pipeline_dir / 'pipeline.yaml'
        
        if not config_file.exists():
            print(f"Pipeline configuration not found: {config_file}")
            return
            
        try:
            with open(config_file, 'r') as f:
                pipeline_config = yaml.safe_load(f) or {}
                
            print(f"Pipeline: {current_pipeline}")
            print(f"Directory: {pipeline_dir}")
            
            packages = pipeline_config.get('packages', [])
            if packages:
                print("Packages:")
                for pkg_def in packages:
                    pkg_id = pkg_def.get('pkg_id', 'unknown')
                    pkg_type = pkg_def.get('pkg_type', 'unknown')
                    global_id = pkg_def.get('global_id', pkg_id)
                    config = pkg_def.get('config', {})
                    
                    print(f"  {pkg_id}:")
                    print(f"    Type: {pkg_type}")
                    print(f"    Global ID: {global_id}")
                    
                    # Display configuration in a more readable format
                    if config:
                        print("    Configuration:")
                        self._print_package_config(pkg_def, "      ")
                    else:
                        print("    Configuration: None")
            else:
                print("No packages in pipeline")
                
            env = pipeline_config.get('env', {})
            if env:
                print("Environment:")
                for key, value in env.items():
                    print(f"  {key}: {value}")
                    
            last_loaded = pipeline_config.get('last_loaded_file')
            if last_loaded:
                print(f"Last loaded from: {last_loaded}")
                
        except Exception as e:
            print(f"Error reading pipeline configuration: {e}")
            
    def change_current_pipeline(self, pipeline_name: str):
        """Change the current pipeline"""
        pipeline_dir = self.jarvis_config.get_pipeline_dir(pipeline_name)
        
        if not pipeline_dir.exists():
            print(f"Pipeline '{pipeline_name}' not found.")
            self.list_pipelines()
            return
            
        config_file = pipeline_dir / 'pipeline.yaml'
        if not config_file.exists():
            print(f"Pipeline '{pipeline_name}' exists but has no configuration file.")
            print("You may need to recreate this pipeline.")
            return
            
        # Set current pipeline in configuration
        self.jarvis_config.set_current_pipeline(pipeline_name)
        
        print(f"Switched to pipeline: {pipeline_name}")
        
        # Show basic info about the pipeline
        try:
            with open(config_file, 'r') as f:
                pipeline_config = yaml.safe_load(f) or {}
                
            num_packages = len(pipeline_config.get('packages', []))
            print(f"Pipeline has {num_packages} packages")
            
        except Exception as e:
            print(f"Warning: Could not read pipeline configuration: {e}")
            
    def _print_package_config(self, pkg_def: Dict[str, Any], indent: str = ""):
        """Print package configuration in a readable format with descriptions"""
        config = pkg_def.get('config', {})
        
        if not config:
            print(f"{indent}No configuration set")
            return
            
        # Try to load the package instance to get configuration menu for descriptions
        config_menu = []
        try:
            pkg_instance = self._load_package_instance(pkg_def)
            if hasattr(pkg_instance, '_configure_menu'):
                config_menu = pkg_instance._configure_menu()
        except Exception:
            # If we can't load the package, just show the raw config
            pass
            
        # Create a lookup for config descriptions
        config_descriptions = {}
        for menu_item in config_menu:
            name = menu_item.get('name')
            msg = menu_item.get('msg', '')
            config_descriptions[name] = msg
            
        # Display each configuration option
        for key, value in config.items():
            description = config_descriptions.get(key, '')
            
            # Format the value nicely
            if isinstance(value, bool):
                value_str = "Yes" if value else "No"
            elif isinstance(value, (list, dict)):
                value_str = str(value)
            elif value is None:
                value_str = "None"
            else:
                value_str = str(value)
                
            # Print with description if available
            if description:
                print(f"{indent}{key}: {value_str}")
                print(f"{indent}  ({description})")
            else:
                print(f"{indent}{key}: {value_str}")
                
    def _get_package_default_config(self, package_spec: str) -> Dict[str, Any]:
        """Get default configuration values for a package"""
        try:
            # Create a temporary package definition to load the package
            temp_pkg_def = {
                'pkg_type': package_spec,
                'pkg_id': 'temp',
                'pkg_name': package_spec.split('.')[-1],
                'global_id': 'temp.temp',
                'config': {}
            }
            
            # Load package instance
            pkg_instance = self._load_package_instance(temp_pkg_def)
            
            # Get configuration menu
            if hasattr(pkg_instance, '_configure_menu'):
                config_menu = pkg_instance._configure_menu()
                
                # Extract default values
                default_config = {}
                for menu_item in config_menu:
                    name = menu_item.get('name')
                    default_value = menu_item.get('default')
                    
                    # Only include items that have default values
                    if name and default_value is not None:
                        default_config[name] = default_value
                
                # Add common parameters that packages might expect
                default_config.setdefault('do_dbg', False)
                default_config.setdefault('dbg_port', 50000)
                        
                return default_config
                
        except Exception as e:
            # If we can't load the package or get defaults, return empty config
            print(f"Warning: Could not load default configuration for {package_spec}: {e}")
            
        return {}
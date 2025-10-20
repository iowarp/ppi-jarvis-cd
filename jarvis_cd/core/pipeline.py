"""
Pipeline management for Jarvis-CD.
Provides the consolidated Pipeline class that combines pipeline creation, loading, and execution.
"""

import os
import yaml
import copy
from pathlib import Path
from typing import Dict, Any, List, Optional
from jarvis_cd.core.config import JarvisConfig, load_class, Jarvis
from jarvis_cd.util.logger import logger


class Pipeline:
    """
    Consolidated pipeline management class.
    Handles pipeline creation, loading, running, and lifecycle management.
    """
    
    def __init__(self, name: str = None):
        """
        Initialize pipeline instance.

        :param name: Pipeline name (optional for new pipelines)
        """
        self.jarvis = Jarvis.get_instance()
        self.name = name
        self.packages = []
        self.interceptors = {}  # Store pipeline-level interceptors by name
        self.env = {}
        self.created_at = None
        self.last_loaded_file = None
        self.shm_container = None  # Container for shared memory IPC
        self.shm_size = "8g"  # Default shared memory size
        
        # Load existing pipeline if name is provided
        if name:
            self.load()
    
    def create(self, pipeline_name: str):
        """
        Create a new pipeline.

        :param pipeline_name: Name of the pipeline to create
        """
        self.name = pipeline_name

        # Create all three directories for the pipeline
        pipeline_config_dir = self.jarvis.jarvis_config.get_pipeline_dir(pipeline_name)
        pipeline_shared_dir = self.jarvis.jarvis_config.get_pipeline_shared_dir(pipeline_name)
        pipeline_private_dir = self.jarvis.jarvis_config.get_pipeline_private_dir(pipeline_name)

        pipeline_config_dir.mkdir(parents=True, exist_ok=True)
        pipeline_shared_dir.mkdir(parents=True, exist_ok=True)
        pipeline_private_dir.mkdir(parents=True, exist_ok=True)

        # Initialize pipeline state
        self.packages = []
        self.interceptors = {}
        self.env = {}
        self.created_at = str(Path().cwd())
        self.last_loaded_file = None

        # Save pipeline configuration and environment
        self.save()

        # Set as current pipeline
        self.jarvis.jarvis_config.set_current_pipeline(pipeline_name)

        print(f"Created pipeline: {pipeline_name}")
        print(f"Config directory: {pipeline_config_dir}")
        print(f"Shared directory: {pipeline_shared_dir}")
        print(f"Private directory: {pipeline_private_dir}")
        
    def load(self, load_type: str = None, pipeline_file: str = None):
        """
        Load pipeline from file or current configuration.
        
        :param load_type: Type of pipeline file (e.g., 'yaml')
        :param pipeline_file: Path to pipeline file
        """
        if load_type and pipeline_file:
            self._load_from_file(load_type, pipeline_file)
        elif self.name:
            self._load_from_config()
        else:
            raise ValueError("No pipeline name or file specified")
    
    def save(self):
        """
        Save pipeline configuration and environment to separate files.

        Creates two YAML files:
        - pipeline.yaml: Contains package/interceptor configuration in script format
        - environment.yaml: Contains environment variables only
        """
        if not self.name:
            raise ValueError("Pipeline name not set")

        pipeline_dir = self.jarvis.jarvis_config.get_pipeline_dir(self.name)
        pipeline_dir.mkdir(parents=True, exist_ok=True)

        # Create pipeline configuration in the SAME format as pipeline scripts
        # This allows code reuse by using the same parsing logic
        pipeline_config = {
            'name': self.name,
            'pkgs': [],
            'interceptors': []
        }

        # Add metadata fields
        if self.created_at:
            pipeline_config['created_at'] = self.created_at
        if self.last_loaded_file:
            pipeline_config['last_loaded_file'] = self.last_loaded_file
        if self.shm_container:
            pipeline_config['shm_container'] = self.shm_container
        if self.shm_size:
            pipeline_config['shm_size'] = self.shm_size

        # Convert packages to script format (pkg_type + config parameters)
        for pkg in self.packages:
            pkg_entry = {
                'pkg_type': pkg['pkg_type']
            }
            # Add pkg_name if different from pkg_type
            if pkg['pkg_id'] != pkg['pkg_name']:
                pkg_entry['pkg_name'] = pkg['pkg_id']

            # Add all config parameters except internal ones
            config = pkg.get('config', {})
            for key, value in config.items():
                pkg_entry[key] = value

            pipeline_config['pkgs'].append(pkg_entry)

        # Convert interceptors to script format
        for interceptor_id, interceptor_def in self.interceptors.items():
            interceptor_entry = {
                'pkg_type': interceptor_def['pkg_type']
            }
            # Add pkg_name if different from pkg_type
            if interceptor_id != interceptor_def['pkg_name']:
                interceptor_entry['pkg_name'] = interceptor_id

            # Add all config parameters
            config = interceptor_def.get('config', {})
            for key, value in config.items():
                interceptor_entry[key] = value

            pipeline_config['interceptors'].append(interceptor_entry)

        # Save pipeline configuration (same format as pipeline scripts)
        config_file = pipeline_dir / 'pipeline.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(pipeline_config, f, default_flow_style=False)

        # Save environment to separate file
        env_file = pipeline_dir / 'environment.yaml'
        with open(env_file, 'w') as f:
            yaml.dump(self.env, f, default_flow_style=False)
    
    def destroy(self, pipeline_name: str = None):
        """
        Destroy a pipeline by removing its directory and configuration.
        If no pipeline name is provided, destroy the current pipeline.
        
        :param pipeline_name: Name of pipeline to destroy (optional)
        """
        # Determine which pipeline to destroy
        if pipeline_name is None:
            if not self.name:
                current_pipeline = self.jarvis.jarvis_config.get_current_pipeline()
                if not current_pipeline:
                    print("No current pipeline to destroy. Specify a pipeline name or create/switch to one first.")
                    return
                pipeline_name = current_pipeline
            else:
                pipeline_name = self.name
                
        target_pipeline_dir = self.jarvis.jarvis_config.get_pipeline_dir(pipeline_name)
        current_pipeline = self.jarvis.jarvis_config.get_current_pipeline()
        is_current = (pipeline_name == current_pipeline)
        
        # Check if pipeline exists
        if not target_pipeline_dir.exists():
            print(f"Pipeline '{pipeline_name}' not found.")
            return
        
        # Try to clean packages first if pipeline is loadable
        config_file = target_pipeline_dir / 'pipeline.yaml'
        if config_file.exists():
            try:
                # Load and clean pipeline
                temp_pipeline = Pipeline(pipeline_name)
                print("Attempting to clean package data before destruction...")
                temp_pipeline.clean()
            except Exception as e:
                print(f"Warning: Could not clean packages before destruction: {e}")
        
        # Remove pipeline directory
        import shutil
        try:
            shutil.rmtree(target_pipeline_dir)
            print(f"Destroyed pipeline: {pipeline_name}")
            
            # Clear current pipeline if we destroyed it
            if is_current:
                config = self.jarvis.jarvis_config.config.copy()
                config['current_pipeline'] = None
                self.jarvis.jarvis_config.save_config(config)
                print("Cleared current pipeline (destroyed pipeline was active)")
                
        except Exception as e:
            print(f"Error destroying pipeline directory: {e}")
    
    def start(self):
        """Start all packages in the pipeline"""
        from jarvis_cd.util.logger import logger, Color

        logger.pipeline(f"Starting pipeline: {self.name}")

        # Start each package with environment propagation
        for pkg_def in self.packages:
            try:
                # Print BEGIN message
                logger.success(f"[{pkg_def['pkg_type']}] [START] BEGIN")

                pkg_instance = self._load_package_instance(pkg_def, self.env)

                # Apply interceptors to this package before starting
                self._apply_interceptors_to_package(pkg_instance, pkg_def)

                if hasattr(pkg_instance, 'start'):
                    pkg_instance.start()
                else:
                    logger.warning(f"Package {pkg_def['pkg_id']} has no start method")

                # Propagate environment changes to next packages
                self.env.update(pkg_instance.env)

                # Print END message
                logger.success(f"[{pkg_def['pkg_type']}] [START] END")

            except Exception as e:
                logger.error(f"Error starting package {pkg_def['pkg_id']}: {e}")
                raise RuntimeError(f"Pipeline startup failed at package '{pkg_def['pkg_id']}': {e}") from e
    
    def stop(self):
        """Stop all packages in the pipeline"""
        from jarvis_cd.util.logger import logger, Color

        logger.pipeline(f"Stopping pipeline: {self.name}")

        # Stop each package in reverse order
        for pkg_def in reversed(self.packages):
            try:
                # Print BEGIN message
                logger.success(f"[{pkg_def['pkg_type']}] [STOP] BEGIN")

                pkg_instance = self._load_package_instance(pkg_def, self.env)

                if hasattr(pkg_instance, 'stop'):
                    pkg_instance.stop()
                else:
                    logger.warning(f"Package {pkg_def['pkg_id']} has no stop method")

                # Print END message
                logger.success(f"[{pkg_def['pkg_type']}] [STOP] END")

            except Exception as e:
                logger.error(f"Error stopping package {pkg_def['pkg_id']}: {e}")
    
    def kill(self):
        """Force kill all packages in the pipeline"""
        from jarvis_cd.util.logger import logger, Color

        logger.pipeline(f"Killing pipeline: {self.name}")

        # Kill each package
        for pkg_def in self.packages:
            try:
                # Print BEGIN message
                logger.success(f"[{pkg_def['pkg_type']}] [KILL] BEGIN")

                pkg_instance = self._load_package_instance(pkg_def, self.env)

                if hasattr(pkg_instance, 'kill'):
                    pkg_instance.kill()
                else:
                    logger.warning(f"Package {pkg_def['pkg_id']} has no kill method")

                # Print END message
                logger.success(f"[{pkg_def['pkg_type']}] [KILL] END")

            except Exception as e:
                logger.error(f"Error killing package {pkg_def['pkg_id']}: {e}")
    
    def status(self) -> str:
        """Get status of the pipeline and its packages"""
        from jarvis_cd.util.logger import logger, Color

        if not self.name:
            return "No pipeline loaded"

        status_info = [f"Pipeline: {self.name}"]
        status_info.append("Packages:")

        # Show status for all packages
        for pkg_def in self.packages:
            try:
                # Print BEGIN message
                logger.success(f"[{pkg_def['pkg_type']}] [STATUS] BEGIN")

                pkg_instance = self._load_package_instance(pkg_def, self.env)

                if pkg_instance and hasattr(pkg_instance, 'status'):
                    pkg_status = pkg_instance.status()
                    status_info.append(f"  {pkg_def['pkg_id']}: {pkg_status}")
                else:
                    status_info.append(f"  {pkg_def['pkg_id']}: no status method")

                # Print END message
                logger.success(f"[{pkg_def['pkg_type']}] [STATUS] END")

            except Exception as e:
                status_info.append(f"  {pkg_def['pkg_id']}: error ({e})")

        return "\n".join(status_info)
    
    def run(self, load_type: Optional[str] = None, pipeline_file: Optional[str] = None):
        """
        Run the pipeline (start all packages, then stop them).
        Optionally load a pipeline file first.

        :param load_type: Type of pipeline file to load (e.g., 'yaml')
        :param pipeline_file: Path to pipeline file to load and run
        """
        try:
            # Load pipeline file if specified
            if load_type and pipeline_file:
                self.load(load_type, pipeline_file)

            self.start()
            logger.pipeline("Pipeline started successfully. Stopping packages...")
            self.stop()
        except Exception as e:
            logger.error(f"Error during pipeline run: {e}")
            logger.info("Attempting to stop packages...")
            try:
                self.stop()
            except Exception as stop_error:
                logger.error(f"Error during cleanup: {stop_error}")
            # Re-raise the original error after cleanup
            raise

    def configure_all_packages(self):
        """
        Configure all packages and interceptors in the pipeline.
        This method loads each package/interceptor instance and calls its configure() method,
        then updates the pipeline environment and saves the configuration.
        """
        print("Configuring interceptors and packages...")

        # Configure interceptors
        for interceptor_id, interceptor_def in self.interceptors.items():
            self._configure_package_instance(interceptor_def, "interceptor")

        # Configure packages
        for pkg_def in self.packages:
            self._configure_package_instance(pkg_def, "package")

        # Save pipeline after configuration
        self.save()
        print("Pipeline configuration saved")

    def _configure_package_instance(self, pkg_def: Dict[str, Any], pkg_type_label: str):
        """
        Configure a single package or interceptor instance.

        :param pkg_def: Package definition dictionary
        :param pkg_type_label: Label for logging ("package" or "interceptor")
        """
        from jarvis_cd.util.logger import logger, Color

        try:
            # Print BEGIN message
            logger.success(f"[{pkg_def['pkg_type']}] [CONFIGURE] BEGIN")

            pkg_instance = self._load_package_instance(pkg_def, self.env)
            if hasattr(pkg_instance, 'configure'):
                # Configure the package with its config
                updated_config = pkg_instance.configure(**pkg_instance.config)

                # Update pkg_def with the final config from the package
                if updated_config:
                    pkg_def['config'] = updated_config
                else:
                    pkg_def['config'] = pkg_instance.config.copy()

                # Update the package environment in the pipeline's env
                self.env.update(pkg_instance.env)

            # Print END message
            logger.success(f"[{pkg_def['pkg_type']}] [CONFIGURE] END")

        except Exception as e:
            import traceback
            logger.error(f"Error configuring {pkg_type_label} {pkg_def['pkg_id']}: {e}")
            logger.error("Full traceback:")
            traceback.print_exc()
            raise
    
    def append(self, package_spec: str, package_alias: Optional[str] = None):
        """
        Append a package to the pipeline.
        
        :param package_spec: Package specification (repo.pkg or just pkg)
        :param package_alias: Optional alias for the package
        """
        if not self.name:
            raise ValueError("No pipeline loaded. Create one with create() first")
            
        # Parse package specification
        if '.' in package_spec:
            repo_name, pkg_name = package_spec.split('.', 1)
        else:
            # Try to find package in available repos
            pkg_name = package_spec
            full_spec = self.jarvis.jarvis_config.find_package(pkg_name)
            if not full_spec:
                raise ValueError(f"Package not found: {pkg_name}")
            package_spec = full_spec
            
        # Determine package ID
        if package_alias:
            pkg_id = package_alias
        else:
            pkg_id = pkg_name
            
        # Check for duplicate package IDs
        existing_ids = [pkg['pkg_id'] for pkg in self.packages]
        if pkg_id in existing_ids:
            raise ValueError(f"Package ID already exists in pipeline: {pkg_id}")
            
        # Get default configuration from package
        default_config = self._get_package_default_config(package_spec)
        
        # Validate that all required parameters have values
        self._validate_required_config(package_spec, default_config)
        
        # Add package to pipeline
        package_entry = {
            'pkg_type': package_spec,
            'pkg_id': pkg_id,
            'pkg_name': pkg_name,
            'global_id': f"{self.name}.{pkg_id}",
            'config': default_config
        }
        
        self.packages.append(package_entry)
        
        # Save updated configuration
        self.save()
            
        print(f"Added package {package_spec} as {pkg_id} to pipeline")
    
    def rm(self, package_spec: str):
        """
        Remove a package from the pipeline.
        
        :param package_spec: Package specification to remove (pkg_id)
        """
        # Find and remove the package
        package_found = False
        
        for i, pkg_def in enumerate(self.packages):
            if pkg_def['pkg_id'] == package_spec:
                removed_package = self.packages.pop(i)
                package_found = True
                break
                
        if not package_found:
            # List available packages to help the user
            available_ids = [pkg['pkg_id'] for pkg in self.packages]
            if available_ids:
                print(f"Package '{package_spec}' not found in pipeline.")
                print(f"Available packages: {', '.join(available_ids)}")
            else:
                print("No packages in pipeline.")
            return
            
        # Save updated configuration
        self.save()
            
        print(f"Removed package '{removed_package['pkg_id']}' ({removed_package['pkg_type']}) from pipeline '{self.name}'")
    
    def clean(self):
        """Clean all data for packages in the pipeline"""
        from jarvis_cd.util.logger import logger, Color

        logger.pipeline(f"Cleaning pipeline: {self.name}")

        # Clean each package
        for pkg_def in self.packages:
            try:
                # Print BEGIN message
                logger.success(f"[{pkg_def['pkg_type']}] [CLEAN] BEGIN")

                pkg_instance = self._load_package_instance(pkg_def, self.env)

                if hasattr(pkg_instance, 'clean'):
                    pkg_instance.clean()
                else:
                    logger.warning(f"Package {pkg_def['pkg_id']} has no clean method")

                # Print END message
                logger.success(f"[{pkg_def['pkg_type']}] [CLEAN] END")

            except Exception as e:
                logger.error(f"Error cleaning package {pkg_def['pkg_id']}: {e}")
    
    def configure_package(self, pkg_id: str, config_args: List[str]):
        """
        Configure a specific package in the pipeline.

        :param pkg_id: Package ID to configure
        :param config_args: Configuration arguments as command-line args (e.g., ['--nprocs', '4', 'block=32m'])
        """
        # Find package in pipeline
        pkg_def = None
        for pkg in self.packages:
            if pkg['pkg_id'] == pkg_id:
                pkg_def = pkg
                break

        if not pkg_def:
            raise ValueError(f"Package not found: {pkg_id}")

        # Load package instance
        pkg_instance = self._load_package_instance(pkg_def, self.env)

        try:
            # Use PkgArgParse to parse and convert arguments
            argparse = pkg_instance.get_argparse()
            # Parse arguments - prepend 'configure' command
            parsed_args = argparse.parse(['configure'] + config_args)
            converted_args = argparse.kwargs

            # Update package configuration with converted values
            pkg_def['config'].update(converted_args)

            # Configure the package instance
            if hasattr(pkg_instance, 'configure'):
                pkg_instance.configure(**converted_args)
                print(f"Configured package {pkg_id} successfully")
            else:
                print(f"Package {pkg_id} has no configure method")

            # Save updated pipeline
            self.save()
            print(f"Saved configuration for {pkg_id}")

        except Exception as e:
            print(f"Error configuring package {pkg_id}: {e}")
            # Show available configuration options
            argparse = pkg_instance.get_argparse()
            argparse.print_help('configure')
    
    def show_package_readme(self, pkg_id: str):
        """
        Show README for a specific package in the pipeline.
        
        :param pkg_id: Package ID to show README for
        """
        # Find package in pipeline
        pkg_def = None
        for pkg in self.packages:
            if pkg['pkg_id'] == pkg_id:
                pkg_def = pkg
                break
                
        if not pkg_def:
            raise ValueError(f"Package not found: {pkg_id}")
        
        # Load package instance and delegate to it
        try:
            pkg_instance = self._load_package_instance(pkg_def, self.env)
            pkg_instance.show_readme()
        except Exception as e:
            print(f"Error showing README for package {pkg_id}: {e}")
    
    def show_package_paths(self, pkg_id: str, path_flags: Dict[str, bool]):
        """
        Show directory paths for a specific package in the pipeline.
        
        :param pkg_id: Package ID to show paths for
        :param path_flags: Dictionary of path flags to show
        """
        # Find package in pipeline
        pkg_def = None
        for pkg in self.packages:
            if pkg['pkg_id'] == pkg_id:
                pkg_def = pkg
                break
                
        if not pkg_def:
            raise ValueError(f"Package not found: {pkg_id}")
        
        # Load package instance and delegate to it
        try:
            pkg_instance = self._load_package_instance(pkg_def, self.env)
            pkg_instance.show_paths(path_flags)
        except Exception as e:
            print(f"Error showing paths for package {pkg_id}: {e}")
    
    def _load_from_config(self):
        """
        Load pipeline from its configuration files.

        Loads from two separate files:
        - pipeline.yaml: Contains package/interceptor configuration in script format
        - environment.yaml: Contains environment variables only
        """
        pipeline_dir = self.jarvis.jarvis_config.get_pipeline_dir(self.name)
        config_file = pipeline_dir / 'pipeline.yaml'

        if not config_file.exists():
            raise FileNotFoundError(f"Pipeline configuration not found: {config_file}")

        # Load pipeline configuration (in script format)
        with open(config_file, 'r') as f:
            pipeline_config = yaml.safe_load(f)

        # Extract metadata
        self.created_at = pipeline_config.get('created_at')
        self.last_loaded_file = pipeline_config.get('last_loaded_file')
        self.shm_container = pipeline_config.get('shm_container')
        self.shm_size = pipeline_config.get('shm_size', '8g')

        # Initialize packages and interceptors
        self.packages = []
        self.interceptors = {}

        # Process interceptors from script format
        interceptors_list = pipeline_config.get('interceptors', [])
        for interceptor_def in interceptors_list:
            interceptor_id = interceptor_def.get('pkg_name', interceptor_def['pkg_type'].split('.')[-1])
            interceptor_entry = self._process_package_definition(interceptor_def, interceptor_id)
            self.interceptors[interceptor_id] = interceptor_entry

        # Process packages from script format
        for pkg_def in pipeline_config.get('pkgs', []):
            pkg_id = pkg_def.get('pkg_name', pkg_def['pkg_type'].split('.')[-1])
            package_entry = self._process_package_definition(pkg_def, pkg_id)
            self.packages.append(package_entry)

        # Load environment from separate file
        env_file = pipeline_dir / 'environment.yaml'
        if env_file.exists():
            with open(env_file, 'r') as f:
                env_config = yaml.safe_load(f)
                if env_config:
                    self.env = env_config
                else:
                    self.env = {}
        else:
            self.env = {}
    
    def _load_from_file(self, load_type: str, pipeline_file: str):
        """Load pipeline from a file"""
        if load_type != 'yaml':
            raise ValueError(f"Unsupported pipeline file type: {load_type}")
            
        pipeline_file = Path(pipeline_file)
        if not pipeline_file.exists():
            raise FileNotFoundError(f"Pipeline file not found: {pipeline_file}")
            
        # Load pipeline definition
        with open(pipeline_file, 'r') as f:
            pipeline_def = yaml.safe_load(f)
            
        self.name = pipeline_def.get('name', pipeline_file.stem)
        
        # Handle environment - can be a string (named env) or missing (auto-build)
        # Inline dictionaries are NOT supported
        env_field = pipeline_def.get('env')

        if env_field is None:
            # No env field defined - automatically build environment
            try:
                from jarvis_cd.core.environment import EnvironmentManager
                env_manager = EnvironmentManager(self.jarvis.jarvis_config)
                self.env = env_manager._capture_current_environment()
                print(f"Auto-built environment with {len(self.env)} variables (no 'env' field in pipeline)")
            except Exception as e:
                print(f"Warning: Could not auto-build environment: {e}")
                self.env = {}
        elif isinstance(env_field, str):
            # Reference to named environment
            env_name = env_field
            try:
                from jarvis_cd.core.environment import EnvironmentManager
                env_manager = EnvironmentManager(self.jarvis.jarvis_config)
                self.env = env_manager.load_named_environment(env_name)
            except Exception as e:
                # Named environment doesn't exist - build it automatically
                print(f"Named environment '{env_name}' does not exist. Building it now...")
                try:
                    from jarvis_cd.core.environment import EnvironmentManager
                    env_manager = EnvironmentManager(self.jarvis.jarvis_config)
                    # Build the named environment from current environment (no additional args)
                    env_manager.build_named_environment(env_name, [])
                    # Now load the newly created environment
                    self.env = env_manager.load_named_environment(env_name)
                    print(f"Built named environment '{env_name}' with {len(self.env)} variables")
                except Exception as build_error:
                    print(f"Warning: Could not build named environment '{env_name}': {build_error}")
                    self.env = {}
        elif isinstance(env_field, dict):
            # Inline environment dictionaries are not allowed
            raise ValueError(
                "Inline environment dictionaries are not supported in pipeline YAML files.\n"
                "The 'env' field must be either:\n"
                "  1. A string referencing a named environment (e.g., env: production_environment)\n"
                "  2. Omitted to auto-build from the current shell environment\n\n"
                "To use custom environment variables:\n"
                "  Option 1 - Create a named environment (reusable across pipelines):\n"
                "    1. Create: jarvis env build <env_name> <commands...>\n"
                "    2. Reference in pipeline YAML: env: <env_name>\n\n"
                "  Option 2 - Build environment for current pipeline (pipeline-specific):\n"
                "    1. Load pipeline: jarvis ppl load yaml <pipeline.yaml>\n"
                "    2. Build environment: jarvis ppl env build <commands...>\n"
                "    3. Pipeline will use the built environment automatically"
            )
        else:
            raise ValueError(
                f"Invalid 'env' field type: {type(env_field).__name__}. "
                "The 'env' field must be either a string (named environment) or omitted (auto-build)."
            )
        
        # Initialize other attributes
        self.created_at = str(Path().cwd())
        self.last_loaded_file = str(pipeline_file.absolute())
        self.packages = []
        self.interceptors = {}  # Store pipeline-level interceptors by name
        self.shm_container = pipeline_def.get('shm_container')
        self.shm_size = pipeline_def.get('shm_size', '8g')
        
        # Process interceptors
        interceptors_list = pipeline_def.get('interceptors', [])
        for interceptor_def in interceptors_list:
            interceptor_id = interceptor_def.get('pkg_name', interceptor_def['pkg_type'].split('.')[-1])
            interceptor_entry = self._process_package_definition(interceptor_def, interceptor_id)
            self.interceptors[interceptor_id] = interceptor_entry

        # Process packages
        for pkg_def in pipeline_def.get('pkgs', []):
            pkg_id = pkg_def.get('pkg_name', pkg_def['pkg_type'])
            package_entry = self._process_package_definition(pkg_def, pkg_id)
            self.packages.append(package_entry)
        
        # Validate that interceptor and package IDs are unique
        self._validate_unique_ids()
        
        # Save pipeline configuration and environment
        self.save()
        
        # Set as current pipeline
        self.jarvis.jarvis_config.set_current_pipeline(self.name)
        
        print(f"Loaded pipeline: {self.name}")
        print(f"Packages: {[pkg['pkg_id'] for pkg in self.packages]}")
    
    def _load_package_instance(self, pkg_def: Dict[str, Any], pipeline_env: Optional[Dict[str, str]] = None):
        """
        Load a package instance from package definition.
        
        :param pkg_def: Package definition dictionary
        :param pipeline_env: Pipeline environment variables
        :return: Package instance
        """
        from jarvis_cd.core.pkg import Pkg
        
        pkg_type = pkg_def['pkg_type']
        
        # Find package class
        if '.' in pkg_type:
            # Full specification like "builtin.ior"
            import_parts = pkg_type.split('.')
            repo_name = import_parts[0]
            pkg_name = import_parts[1]
        else:
            # Just package name, search in repos
            full_spec = self.jarvis.jarvis_config.find_package(pkg_type)
            if not full_spec:
                raise ValueError(f"Package not found: {pkg_type}")
            import_parts = full_spec.split('.')
            repo_name = import_parts[0]
            pkg_name = import_parts[1]
            
        # Determine class name (convert snake_case to PascalCase)
        class_name = ''.join(word.capitalize() for word in pkg_name.split('_'))
        
        # Load class
        if repo_name == 'builtin':
            repo_path = str(self.jarvis.jarvis_config.get_builtin_repo_path())
        else:
            # Find repo path in registered repos
            repo_path = None
            for registered_repo in self.jarvis.jarvis_config.repos['repos']:
                if Path(registered_repo).name == repo_name:
                    repo_path = registered_repo
                    break
                    
            if not repo_path:
                raise ValueError(f"Repository not found: {repo_name}")
                
        import_str = f"{repo_name}.{pkg_name}.pkg"
        try:
            pkg_class = load_class(import_str, repo_path, class_name)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            raise ValueError(
                f"Failed to load package '{pkg_type}':\n"
                f"  Repository: {repo_name}\n"
                f"  Package: {pkg_name}\n"
                f"  Repo path: {repo_path}\n"
                f"  Import string: {import_str}\n"
                f"  Class name: {class_name}\n"
                f"  Error: {e}\n"
                f"  Traceback:\n{error_details}"
            )

        if not pkg_class:
            raise ValueError(f"Package class not found: {class_name} in {import_str}")

        # Create instance with pipeline context
        try:
            pkg_instance = pkg_class(pipeline=self)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            raise ValueError(
                f"Failed to instantiate package '{pkg_type}':\n"
                f"  Class: {class_name}\n"
                f"  Error during __init__: {e}\n"
                f"  Traceback:\n{error_details}"
            )

        # Set basic attributes
        pkg_instance.pkg_type = pkg_def['pkg_type']
        pkg_instance.pkg_id = pkg_def['pkg_id']
        pkg_instance.global_id = pkg_def['global_id']

        # Initialize directories now that pkg_id is set
        pkg_instance._ensure_directories()

        # Set configuration
        base_config = pkg_def.get('config', {})
        base_config.setdefault('do_dbg', False)
        base_config.setdefault('dbg_port', 50000)
        pkg_instance.config = base_config
            
        # Set up environment variables - mod_env is exact replica of env plus LD_PRELOAD
        if pipeline_env is None:
            pipeline_env = {}

        # env contains everything except LD_PRELOAD
        pkg_instance.env = {k: v for k, v in pipeline_env.items() if k != 'LD_PRELOAD'}

        # mod_env is exact replica of env plus LD_PRELOAD (if it exists)
        pkg_instance.mod_env = pkg_instance.env.copy()
        if 'LD_PRELOAD' in pipeline_env:
            pkg_instance.mod_env['LD_PRELOAD'] = pipeline_env['LD_PRELOAD']

        return pkg_instance
    
    def _process_package_definition(self, pkg_def: Dict[str, Any], pkg_id: str) -> Dict[str, Any]:
        """
        Process a package definition from YAML, merging YAML config with defaults.

        :param pkg_def: Package definition from YAML
        :param pkg_id: Package ID to use
        :return: Complete package entry with merged configuration
        """
        pkg_type = pkg_def['pkg_type']

        # Resolve pkg_type to full specification (repo.package) if not already specified
        if '.' not in pkg_type:
            resolved_type = self.jarvis.jarvis_config.find_package(pkg_type)
            if resolved_type:
                pkg_type = resolved_type
            # If not found, keep original (will fail later during loading)

        # Get default configuration from package
        default_config = self._get_package_default_config(pkg_type)

        # Extract config from YAML
        yaml_config = {k: v for k, v in pkg_def.items()
                      if k not in ['pkg_type', 'pkg_name']}

        # Merge YAML config on top of defaults
        merged_config = default_config.copy()
        merged_config.update(yaml_config)

        return {
            'pkg_type': pkg_type,
            'pkg_id': pkg_id,
            'pkg_name': pkg_type.split('.')[-1],
            'global_id': f"{self.name}.{pkg_id}",
            'config': merged_config
        }

    def _get_package_default_config(self, package_spec: str) -> Dict[str, Any]:
        """
        Get default configuration values for a package by parsing with PkgArgParse.
        Equivalent to calling 'configure' with no parameters.
        """
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

            # Use PkgArgParse to get defaults by parsing 'configure' with no args
            argparse = pkg_instance.get_argparse()
            argparse.parse(['configure'])
            default_config = argparse.kwargs

            return default_config

        except Exception as e:
            # Package loading failure should be fatal - cannot add package to pipeline
            raise ValueError(f"Failed to load package '{package_spec}': {e}")

        return {}
    
    def _validate_unique_ids(self):
        """
        Validate that interceptor IDs and package IDs are unique within the pipeline.
        """
        # Get all package IDs
        package_ids = {pkg['pkg_id'] for pkg in self.packages}
        
        # Get all interceptor IDs
        interceptor_ids = set(self.interceptors.keys())
        
        # Check for conflicts
        conflicts = package_ids & interceptor_ids
        if conflicts:
            conflict_list = ', '.join(conflicts)
            raise ValueError(f"ID conflicts between packages and interceptors: {conflict_list}. "
                           f"Package and interceptor IDs must be unique within the pipeline.")
    
    def _validate_required_config(self, package_spec: str, config: Dict[str, Any]):
        """
        Validate that all required configuration parameters have values.
        
        :param package_spec: Package specification 
        :param config: Configuration dictionary
        :raises ValueError: If required parameters are missing or None
        """
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
            
            # Get configuration menu to check for required parameters
            if hasattr(pkg_instance, 'configure_menu'):
                config_menu = pkg_instance.configure_menu()
                if config_menu:
                    missing_required = []
                    for menu_item in config_menu:
                        name = menu_item.get('name')
                        default_value = menu_item.get('default')
                        
                        # If parameter has no default and is not provided in config, it's required
                        if name and default_value is None and (name not in config or config[name] is None):
                            missing_required.append(name)
                    
                    if missing_required:
                        raise ValueError(f"Missing required configuration parameters for {package_spec}: {', '.join(missing_required)}")
                        
        except Exception as e:
            if "Missing required configuration parameters" in str(e):
                raise  # Re-raise our validation error
            # Other errors during validation are not fatal
            print(f"Warning: Could not validate configuration for {package_spec}: {e}")
    
    def _apply_interceptors_to_package(self, pkg_instance, pkg_def):
        """
        Apply interceptors to a package instance during pipeline start.

        :param pkg_instance: The package instance to apply interceptors to
        :param pkg_def: The package definition from pipeline configuration
        """
        from jarvis_cd.util.logger import logger, Color

        # Get interceptors list from package configuration
        interceptors_list = pkg_def.get('config', {}).get('interceptors', [])

        if not interceptors_list:
            return

        logger.warning(f"Applying {len(interceptors_list)} interceptors to {pkg_def['pkg_id']}")

        for interceptor_name in interceptors_list:
            try:
                # Find interceptor in pipeline-level interceptors
                if interceptor_name not in self.interceptors:
                    logger.error(f"Warning: Interceptor '{interceptor_name}' not found in pipeline interceptors")
                    continue

                interceptor_def = self.interceptors[interceptor_name]

                # Print BEGIN message with full interceptor type
                logger.success(f"[{interceptor_def['pkg_type']}] [MODIFY_ENV] BEGIN")

                # Load interceptor instance
                interceptor_instance = self._load_package_instance(interceptor_def, self.env)

                # Verify it's an interceptor and has modify_env method
                if not hasattr(interceptor_instance, 'modify_env'):
                    logger.error(f"Warning: Package '{interceptor_name}' does not have modify_env() method")
                    continue

                # Share the same mod_env reference between interceptor and package
                interceptor_instance.mod_env = pkg_instance.mod_env
                interceptor_instance.env = pkg_instance.env

                # Call modify_env on the interceptor to modify the shared environment
                interceptor_instance.modify_env()

                # The mod_env is shared, so changes are automatically applied to the package

                # Print END message
                logger.success(f"[{interceptor_def['pkg_type']}] [MODIFY_ENV] END")

            except Exception as e:
                logger.error(f"Error applying interceptor '{interceptor_name}': {e}")
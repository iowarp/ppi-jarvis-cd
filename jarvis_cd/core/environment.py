import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from jarvis_cd.core.config import Jarvis


class EnvironmentManager:
    """
    Manages Jarvis environments - both pipeline-specific and named environments.
    """
    
    # Common environment variables that should be captured
    COMMON_ENV_VARS = [
        # Build system variables
        'CMAKE_MODULE_PATH',
        'CMAKE_PREFIX_PATH',
        'PKG_CONFIG_PATH',
        
        # C/C++ include paths
        'CPATH',
        'C_INCLUDE_PATH', 
        'CPLUS_INCLUDE_PATH',
        'INCLUDE_PATH',
        
        # Library paths
        'LD_LIBRARY_PATH',
        'LIBRARY_PATH',
        'DYLD_LIBRARY_PATH',  # macOS
        'LD_PRELOAD',
        
        # Runtime paths
        'PATH',
        'MANPATH',
        
        # Language-specific paths
        'PYTHONPATH',
        'PERL5LIB',
        'CLASSPATH',
        'GOPATH',
        'CARGO_HOME',
        'TCLLIBPATH',
        
        # Development tools
        'JAVA_HOME',
        
        # Compilers
        'CC',
        'CXX', 
        'FC',
        'F77',
        'F90',
        
        # MPI compilers
        'MPICC',
        'MPICXX',
        'MPIFC',
        'MPIF77',
        'MPIF90',
        
        # Other common build variables
        'CFLAGS',
        'CXXFLAGS',
        'FFLAGS',
        'LDFLAGS',
        'LIBS',
    ]
    
    def __init__(self, jarvis_config: Jarvis):
        """
        Initialize environment manager.

        :param jarvis_config: Jarvis configuration singleton
        """
        self.jarvis_config = jarvis_config
        
    def build_pipeline_environment(self, env_args: List[str]):
        """
        Build environment for the current pipeline by capturing current environment
        and adding user-specified variables.
        
        :param env_args: List of environment arguments in VAR=value format
        """
        current_pipeline_dir = self.jarvis_config.get_current_pipeline_dir()
        if not current_pipeline_dir:
            raise ValueError("No current pipeline. Create one with 'jarvis ppl create <name>'")
            
        # Capture current environment
        captured_env = self._capture_current_environment()
        
        # Parse user-provided environment variables
        user_env = self._parse_env_args(env_args)
        
        # Merge environments (user overrides captured)
        final_env = {**captured_env, **user_env}
        
        # Save to pipeline's env.yaml
        env_file = current_pipeline_dir / 'env.yaml'
        with open(env_file, 'w') as f:
            yaml.dump(final_env, f, default_flow_style=False)
            
        print(f"Built environment for current pipeline with {len(final_env)} variables")
        print(f"Captured {len(captured_env)} environment variables")
        print(f"User specified {len(user_env)} additional variables")
        
    def build_named_environment(self, env_name: str, env_args: List[str]):
        """
        Build a named environment that can be reused across pipelines.
        
        :param env_name: Name of the environment
        :param env_args: List of environment arguments in VAR=value format
        """
        # Create env directory if it doesn't exist
        env_dir = self.jarvis_config.jarvis_root / 'env'
        env_dir.mkdir(exist_ok=True)
        
        # Capture current environment
        captured_env = self._capture_current_environment()
        
        # Parse user-provided environment variables
        user_env = self._parse_env_args(env_args)
        
        # Merge environments (user overrides captured)
        final_env = {**captured_env, **user_env}
        
        # Save named environment
        env_file = env_dir / f'{env_name}.yaml'
        with open(env_file, 'w') as f:
            yaml.dump(final_env, f, default_flow_style=False)
            
        print(f"Created named environment '{env_name}' with {len(final_env)} variables")
        print(f"Captured {len(captured_env)} environment variables")
        print(f"User specified {len(user_env)} additional variables")
        print(f"Saved to: {env_file}")
        
    def copy_named_environment(self, env_name: str):
        """
        Copy a named environment to the current pipeline.
        
        :param env_name: Name of the environment to copy
        """
        current_pipeline_dir = self.jarvis_config.get_current_pipeline_dir()
        if not current_pipeline_dir:
            raise ValueError("No current pipeline. Create one with 'jarvis ppl create <name>'")
            
        # Find named environment file
        env_dir = self.jarvis_config.jarvis_root / 'env'
        env_file = env_dir / f'{env_name}.yaml'
        
        if not env_file.exists():
            # List available environments to help user
            available_envs = self.list_named_environments()
            if available_envs:
                print(f"Named environment '{env_name}' not found.")
                print(f"Available environments: {', '.join(available_envs)}")
            else:
                print("No named environments found. Create one with 'jarvis env build <name>'")
            return
            
        # Load named environment
        with open(env_file, 'r') as f:
            named_env = yaml.safe_load(f) or {}
            
        # Copy to pipeline's env.yaml
        pipeline_env_file = current_pipeline_dir / 'env.yaml'
        with open(pipeline_env_file, 'w') as f:
            yaml.dump(named_env, f, default_flow_style=False)
            
        # Get current pipeline name for display
        config_file = current_pipeline_dir / 'pipeline.yaml'
        with open(config_file, 'r') as f:
            pipeline_config = yaml.safe_load(f)
            pipeline_name = pipeline_config['name']
            
        print(f"Copied named environment '{env_name}' to pipeline '{pipeline_name}'")
        print(f"Environment contains {len(named_env)} variables")
        
    def list_named_environments(self) -> List[str]:
        """
        List all available named environments.

        :return: List of environment names
        """
        env_dir = self.jarvis_config.jarvis_root / 'env'
        if not env_dir.exists():
            return []

        env_files = list(env_dir.glob('*.yaml'))
        return [f.stem for f in env_files]

    @staticmethod
    def show_environment(env_file_path: Path, context_name: str):
        """
        Display environment variables from a YAML file.

        This is a unified function used by both pipeline and named environment display.

        :param env_file_path: Path to the environment YAML file
        :param context_name: Name to display in the output (e.g., pipeline name or environment name)
        """
        if not env_file_path.exists():
            print(f"No environment configured for '{context_name}'")
            return

        with open(env_file_path, 'r') as f:
            env_vars = yaml.safe_load(f) or {}

        print(f"Environment for '{context_name}':")
        print(f"Total variables: {len(env_vars)}")
        print()

        if env_vars:
            # Sort by variable name for consistent display
            for var_name in sorted(env_vars.keys()):
                value = env_vars[var_name]
                # Truncate very long values for readability
                if isinstance(value, str) and len(value) > 100:
                    display_value = value[:97] + "..."
                else:
                    display_value = value
                print(f"  {var_name}: {display_value}")
        else:
            print("  No environment variables set")
        
    def show_pipeline_environment(self):
        """
        Show the environment variables for the current pipeline.
        """
        current_pipeline_dir = self.jarvis_config.get_current_pipeline_dir()
        if not current_pipeline_dir:
            print("No current pipeline set")
            return

        # Get current pipeline name for display context
        config_file = current_pipeline_dir / 'pipeline.yaml'
        with open(config_file, 'r') as f:
            pipeline_config = yaml.safe_load(f)
            pipeline_name = pipeline_config['name']

        # Use unified function to display environment
        env_file = current_pipeline_dir / 'env.yaml'
        self.show_environment(env_file, f"pipeline '{pipeline_name}'")
            
    def show_named_environment(self, env_name: str):
        """
        Show the variables in a named environment.

        :param env_name: Name of the environment to show
        """
        env_dir = self.jarvis_config.jarvis_root / 'env'
        env_file = env_dir / f'{env_name}.yaml'

        # Check if environment exists and provide helpful error message
        if not env_file.exists():
            available_envs = self.list_named_environments()
            if available_envs:
                print(f"Named environment '{env_name}' not found.")
                print(f"Available environments: {', '.join(available_envs)}")
            else:
                print("No named environments found")
            return

        # Use unified function to display environment
        self.show_environment(env_file, f"named environment '{env_name}'")
            
    def load_named_environment(self, env_name: str) -> Dict[str, str]:
        """
        Load a named environment and return its variables.
        
        :param env_name: Name of the environment to load
        :return: Dictionary of environment variables
        :raises FileNotFoundError: If the named environment doesn't exist
        """
        env_dir = self.jarvis_config.jarvis_root / 'env'
        env_file = env_dir / f'{env_name}.yaml'
        
        if not env_file.exists():
            available_envs = self.list_named_environments()
            if available_envs:
                error_msg = f"Named environment '{env_name}' not found. Available: {', '.join(available_envs)}"
            else:
                error_msg = f"Named environment '{env_name}' not found. No named environments exist."
            raise FileNotFoundError(error_msg)
            
        with open(env_file, 'r') as f:
            env_vars = yaml.safe_load(f) or {}
            
        return env_vars
            
    def _capture_current_environment(self) -> Dict[str, str]:
        """
        Capture current environment variables that are commonly used in builds.
        
        :return: Dictionary of environment variables
        """
        captured = {}
        
        for var_name in self.COMMON_ENV_VARS:
            if var_name in os.environ:
                captured[var_name] = os.environ[var_name]
                
        return captured
        
    def _parse_env_args(self, env_args: List[str]) -> Dict[str, str]:
        """
        Parse environment arguments in VAR=value format.
        
        :param env_args: List of environment arguments
        :return: Dictionary of parsed environment variables
        """
        parsed = {}
        
        for arg in env_args:
            if '=' in arg:
                key, value = arg.split('=', 1)
                parsed[key] = value
            else:
                print(f"Warning: Ignoring malformed environment argument: {arg}")
                print("Expected format: VAR=value")
                
        return parsed
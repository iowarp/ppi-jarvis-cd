"""
Example Interceptor package for testing interceptor functionality
"""

from jarvis_cd.core.pkg import Interceptor
import os


class ExampleInterceptor(Interceptor):
    """
    Example interceptor that modifies environment variables
    and sets up LD_PRELOAD for demonstration
    """

    def _configure_menu(self):
        """
        Create a CLI menu for the configurator method.
        """
        return [
            {
                'name': 'library_path',
                'msg': 'Path to the interceptor library (if any)',
                'type': str,
                'default': '/tmp/example_interceptor.so'
            },
            {
                'name': 'custom_env_var',
                'msg': 'Custom environment variable value to set',
                'type': str,
                'default': 'intercepted_value'
            },
            {
                'name': 'debug_mode',
                'msg': 'Enable debug output from interceptor',
                'type': bool,
                'default': True
            }
        ]

    def _configure(self, **kwargs):
        """
        Configure the example interceptor
        """
        # Create output directory
        os.makedirs(self.private_dir, exist_ok=True)
        self.log(f'ExampleInterceptor configured with library_path: {self.config["library_path"]}')

    def _init(self):
        """
        Initialize the example interceptor
        """
        pass

    def modify_env(self):
        """
        Modify the jarvis environment to demonstrate interceptor functionality
        """
        self.log('ExampleInterceptor modifying environment')
        
        # Set custom environment variables
        self.setenv('EXAMPLE_INTERCEPTOR_ACTIVE', 'true')
        self.setenv('EXAMPLE_CUSTOM_VAR', self.config['custom_env_var'])
        
        if self.config['debug_mode']:
            self.setenv('EXAMPLE_DEBUG', '1')
            
        # Demonstrate LD_PRELOAD modification (even if library doesn't exist)
        if self.config['library_path']:
            self.log(f'Adding {self.config["library_path"]} to LD_PRELOAD')
            self.prepend_env('LD_PRELOAD', self.config['library_path'])
            
        # Set a path-like environment variable
        example_path = os.path.join(self.private_dir, 'interceptor_libs')
        os.makedirs(example_path, exist_ok=True)
        self.prepend_env('EXAMPLE_LIB_PATH', example_path)
        
        self.log('Environment modifications completed:')
        self.log(f'  EXAMPLE_INTERCEPTOR_ACTIVE = {self.env.get("EXAMPLE_INTERCEPTOR_ACTIVE", "not set")}')
        self.log(f'  EXAMPLE_CUSTOM_VAR = {self.env.get("EXAMPLE_CUSTOM_VAR", "not set")}')
        self.log(f'  LD_PRELOAD = {self.mod_env.get("LD_PRELOAD", "not set")}')
        self.log(f'  EXAMPLE_LIB_PATH = {self.env.get("EXAMPLE_LIB_PATH", "not set")}')
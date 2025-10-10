"""
Example Application package for testing interceptors
"""

from jarvis_cd.core.pkg import Application, Interceptor
from jarvis_cd.shell import Exec, LocalExecInfo
import os


class ExampleApp(Application):
    """
    Example application that prints environment variables
    and creates a simple test file
    """

    def _configure_menu(self):
        """
        Create a CLI menu for the configurator method.
        """
        return [
            {
                'name': 'message',
                'msg': 'Message to print during execution',
                'type': str,
                'default': 'Hello from Example App!'
            },
            {
                'name': 'output_file',
                'msg': 'Output file to create',
                'type': str,
                'default': 'example_output.txt'
            }
        ]

    def _configure(self, **kwargs):
        """
        Configure the example application
        """
        # Create output directory
        os.makedirs(self.private_dir, exist_ok=True)
        os.makedirs(self.shared_dir, exist_ok=True)
        self.output_path = os.path.join(self.private_dir, self.config['output_file'])

        self.log(f'Modified environment variables: {self.mod_env.get("LD_PRELOAD", "None")}')

        # Create marker file for configure command
        marker_path = os.path.join(self.shared_dir, 'configure.marker')
        with open(marker_path, 'w') as f:
            f.write(f'Configured at: {self.config["message"]}\n')
        self.log(f'Created configure marker: {marker_path}')

    def _init(self):
        """
        Initialize the example application
        """
        self.output_path = None

    def start(self):
        """
        Start the example application
        """
        self.log(f'Starting ExampleApp with message: {self.config["message"]}')

        # Create marker file for start command
        marker_path = os.path.join(self.shared_dir, 'start.marker')
        with open(marker_path, 'w') as f:
            f.write(f'Started with message: {self.config["message"]}\n')
        self.log(f'Created start marker: {marker_path}')

        # Create output file as well if output_path is set
        if self.output_path:
            with open(self.output_path, 'w') as f:
                f.write(f'{self.config["message"]}\n')
            self.log(f'Created output file: {self.output_path}')

    def stop(self):
        """
        Stop the application
        """
        self.log('ExampleApp stopped')

        # Create marker file for stop command
        marker_path = os.path.join(self.shared_dir, 'stop.marker')
        with open(marker_path, 'w') as f:
            f.write('Stopped\n')
        self.log(f'Created stop marker: {marker_path}')

    def kill(self):
        """
        Kill the application
        """
        self.log('ExampleApp killed')

        # Create marker file for kill command
        marker_path = os.path.join(self.shared_dir, 'kill.marker')
        with open(marker_path, 'w') as f:
            f.write('Killed\n')
        self.log(f'Created kill marker: {marker_path}')

    def clean(self):
        """
        Clean up application data - this is the 'clear' functionality
        """
        self.log('Cleaning ExampleApp data')

        # Remove all marker files
        marker_files = ['start.marker', 'stop.marker', 'kill.marker', 'configure.marker']
        for marker in marker_files:
            marker_path = os.path.join(self.shared_dir, marker)
            if os.path.exists(marker_path):
                os.remove(marker_path)
                self.log(f'Removed marker file: {marker_path}')

        # Remove output file
        if hasattr(self, 'output_path') and os.path.exists(self.output_path):
            os.remove(self.output_path)
            self.log(f'Removed output file: {self.output_path}')

    def status(self):
        """
        Check if the application completed successfully
        """
        return os.path.exists(self.output_path)

    def modify_env(self):
        """
        Modify environment when used as an interceptor
        """
        self.log('ExampleApp acting as interceptor - setting EXAMPLE_VAR')
        self.setenv('EXAMPLE_VAR', 'test_value_from_interceptor')
        self.setenv('INTERCEPTOR_APPLIED', 'example_app')
        
    def log(self, message):
        """
        Simple logging method
        """
        print(f"[ExampleApp] {message}")
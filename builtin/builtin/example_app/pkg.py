"""
Example Application package for testing interceptors
"""

from jarvis_cd.basic.pkg import Application
from jarvis_util.shell.local_exec import LocalExecInfo
from jarvis_util.shell.exec import Exec
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
        self.output_path = os.path.join(self.private_dir, self.config['output_file'])

    def _init(self):
        """
        Initialize the example application
        """
        pass

    def start(self):
        """
        Start the example application
        """
        self.log(f'Starting ExampleApp with message: {self.config["message"]}')
        
        # Create a simple script to run
        script_content = f'''#!/bin/bash
echo "ExampleApp starting..."
echo "Message: {self.config['message']}"
echo "Current environment variables:"
env | grep -E "(LD_PRELOAD|EXAMPLE_)" || echo "No relevant env vars found"
echo "Creating output file: {self.output_path}"
echo "{self.config['message']}" > "{self.output_path}"
echo "ExampleApp finished successfully"
'''
        
        script_path = os.path.join(self.private_dir, 'run_example.sh')
        with open(script_path, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        
        # Execute the script
        cmd = f'bash {script_path}'
        exec_info = LocalExecInfo(
            env=self.mod_env,
            hide_output=self.config['hide_output']
        )
        
        self.exec = Exec(cmd, exec_info)
        self.exit_code = self.exec.exit_code

    def stop(self):
        """
        Stop the application (nothing to do for this example)
        """
        self.log('ExampleApp stopped')

    def clean(self):
        """
        Clean up application data
        """
        self.log('Cleaning ExampleApp data')
        if os.path.exists(self.output_path):
            os.remove(self.output_path)
            self.log(f'Removed output file: {self.output_path}')

    def status(self):
        """
        Check if the application completed successfully
        """
        return os.path.exists(self.output_path)
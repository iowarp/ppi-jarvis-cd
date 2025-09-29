"""
This module provides classes and methods to launch the MyShell application.
MyShell is ....
"""
from jarvis_cd.core.pkg import Application
from jarvis_cd.shell import Exec, LocalExecInfo


class MyShell(Application):
    """
    This class provides methods to launch the MyShell application.
    """
    def _init(self):
        """
        Initialize paths
        """
        pass

    def _configure_menu(self):
        """
        Create a CLI menu for the configurator method.
        For thorough documentation of these parameters, view:
        https://github.com/scs-lab/jarvis-util/wiki/3.-Argument-Parsing

        :return: List(dict)
        """
        
        return [
            {
                'name': 'script',  # The name of the parameter
                'msg': 'The path of shell script to execute.',  # Describe this parameter
                'type': str,  # What is the parameter type?
                'default': None,  # What is the default value if not required?
            },
        ]

    def _configure(self, **kwargs):
        """
        Converts the Jarvis configuration to application-specific configuration.
        E.g., OrangeFS produces an orangefs.xml file.

        :param kwargs: Configuration parameters for this pkg.
        :return: None
        """
        self.config['script'] = self.config['script']

    def start(self):
        """
        Launch an application. E.g., OrangeFS will launch the servers, clients,
        and metadata services on all necessary pkgs.

        :return: None
        """
        cmd = [
            'bash',
        ]
        if self.config['script']:
            cmd.append(self.config['script'])
        # pipe_stdout=self.config['log']
        Exec(' '.join(cmd), LocalExecInfo()).run()

    def stop(self):
        """
        Stop a running application. E.g., OrangeFS will terminate the servers,
        clients, and metadata services.

        :return: None
        """
        pass

    def clean(self):
        """
        Destroy all data for an application. E.g., OrangeFS will delete all
        metadata and data directories in addition to the orangefs.xml file.

        :return: None
        """
        pass

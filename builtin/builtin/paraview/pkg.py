"""
This module provides classes and methods to launch the Paraview application.
Paraview is ....
"""
from jarvis_cd.core.pkg import Application
from jarvis_cd.shell import Exec, MpiExecInfo


class Paraview(Application):
    """
    This class provides methods to launch the Paraview application.
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
                'name': 'nprocs',
                'msg': 'Number of processes',
                'type': int,
                'default': 1,
            },
            {
                'name': 'ppn',
                'msg': 'The number of processes per node',
                'type': int,
                'default': 16,
            },
            {
                'name': 'time_out',
                'msg': 'Set a timeout period for idle client sessions',
                'type': int,
                'default': 10000,
            },
            {
                'name': 'force_offscreen_rendering',
                'msg': 'Useful for headless environments (no display)',
                'type': bool,
                'default': False,
            },
            {
                'name': 'port_id',
                'msg': 'Set the port the server listens on',
                'type': int,
                'default': 11111,
            },
        ]

    def _configure(self, **kwargs):
        """
        Converts the Jarvis configuration to application-specific configuration.
        E.g., OrangeFS produces an orangefs.xml file.

        :param kwargs: Configuration parameters for this pkg.
        :return: None
        """

        pass

    def start(self):
        """
        Launch an application. E.g., OrangeFS will launch the servers, clients,
        and metadata services on all necessary pkgs.

        :return: None
        """
        port_Id = self.config["port_id"]
        time_out = self.config["time_out"]
        condition = ''
        if self.config['force_offscreen_rendering']:
            condition += ' --force-offscreen-rendering'

        Exec(f'pvserver --server-port={port_Id} --timeout={time_out}{condition}',
             MpiExecInfo(nprocs=self.config['nprocs'],
                         ppn=self.config['ppn'],
                         env=self.mod_env
                        )).run()

        pass

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


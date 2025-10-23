"""
This module provides classes and methods to launch the Ior application.
Ior is ....
"""
from jarvis_cd.core.pkg import Service
from jarvis_cd.shell import PsshExecInfo
from jarvis_cd.shell.process import Mkdir, Kill, Rm
# TODO: Monitor import needs to be resolved - not available in jarvis_cd yet
# from jarvis_util.introspect.monitor import Monitor

class Pymonitor(Service):
    """
    This class provides methods to launch the Ior application.
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
                'name': 'frequency',
                'msg': 'Monitor frequency in seconds',
                'type': int,
                'default': 1
            },
            {
                'name': 'dir',
                'msg': 'Directory to store monitor logs',
                'type': str,
                'default': None,
            },
            {
                'name': 'num_nodes',
                'msg': 'Number of nodes to run monitor on. 0 means all',
                'type': int,
                'default': 0,
            },
        ]

    def _configure(self, **kwargs):
        """
        Converts the Jarvis configuration to application-specific configuration.
        E.g., OrangeFS produces an orangefs.xml file.

        :param kwargs: Configuration parameters for this pkg.
        :return: None
        """
        if self.config['dir'] is None:
            self.config['dir'] = f'{self.shared_dir}/logs'
        self.config['dir'] = os.path.expandvars(self.config['dir'])
        Mkdir(self.config['dir']).run()
        self.env['MONITOR_DIR'] = self.config['dir']
        self.log(f'The config dir is {self.config["dir"]}')

    def start(self):
        """
        Launch an application. E.g., OrangeFS will launch the servers, clients,
        and metadata services on all necessary pkgs.

        :return: None
        """
        self.log(f'Pymonitor started on {self.config["dir"]}')
        self.env['PYTHONBUFFERED'] = '0'
        hostfile = self.hostfile
        if self.config['num_nodes'] > 0:
            hostfile = hostfile.subset(self.config['num_nodes'])
        Monitor(self.config['frequency'],
                self.config['dir'],
                PsshExecInfo(env=self.env,
                            hostfile=hostfile,
                            exec_async=True))
        time.sleep(self.config['sleep'])

    def stop(self):
        """
        Stop a running application. E.g., OrangeFS will terminate the servers,
        clients, and metadata services.

        :return: None
        """
        Kill('.*pymonitor.*', PsshExecInfo(env=self.env)).run()

    def status(self):
        pass

    def clean(self):
        """
        Destroy all data for an application. E.g., OrangeFS will delete all
        metadata and data directories in addition to the orangefs.xml file.

        :return: None
        """
        Rm(self.config['dir']).run()

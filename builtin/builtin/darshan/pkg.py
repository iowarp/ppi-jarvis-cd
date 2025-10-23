"""
This module provides classes and methods to inject the Darshan interceptor.
Darshan is ....
"""
from jarvis_cd.core.pkg import Interceptor
from jarvis_cd.shell import PsshExecInfo
from jarvis_cd.shell.process import Mkdir
import os


class Darshan(Interceptor):
    """
    This class provides methods to inject the Darshan interceptor.
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
                'name': 'log_dir',
                'msg': 'Where darshan should place data',
                'type': str,
                'default': f'{os.getenv("HOME")}/darshan_logs',
            },
            {
                'name': 'job_id',
                'msg': 'A semantic ID for the job to identify log files',
                'type': str,
                'default': 'myjob',
            },
        ]

    def _configure(self, **kwargs):
        """
        Converts the Jarvis configuration to application-specific configuration.
        E.g., OrangeFS produces an orangefs.xml file.

        :param kwargs: Configuration parameters for this pkg.
        :return: None
        """
        self.env['DARSHAN_LOG_DIR'] = self.config['log_dir']
        self.env['PBS_JOBID'] = self.config['job_id']
        self.config['DARSHAN_LIB'] = self.find_library('darshan')
        if self.config['DARSHAN_LIB'] is None:
            raise Exception('Could not find darshan')
        Mkdir(self.env['DARSHAN_LOG_DIR'],
              PsshExecInfo(hostfile=self.hostfile)).run()
        print(f'Found libdarshan.so at {self.config["DARSHAN_LIB"]}')

    def modify_env(self):
        """
        Modify the jarvis environment.

        :return: None
        """
        self.append_env('LD_PRELOAD', self.config['DARSHAN_LIB'])

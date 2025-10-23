"""
This module provides classes and methods to launch the Ior application.
Ior is ....
"""
from jarvis_cd.core.pkg import Application
from jarvis_cd.shell import Exec, LocalExecInfo
from jarvis_cd.shell.process import Rm
import os
import pathlib


class Fio(Application):
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
                'name': 'write',
                'msg': 'Perform a write workload',
                'type': bool,
                'default': True,
                'choices': [],
                'args': [],
            },
            {
                'name': 'read',
                'msg': 'Perform a read workload',
                'type': bool,
                'default': False,
            },
            {
                'name': 'xfer',
                'msg': 'The size of data transfer',
                'type': str,
                'default': '1m',
            },
            {
                'name': 'total_size',
                'msg': 'Total amount of data to generate',
                'type': str,
                'default': '32m',
            },
            {
                'name': 'iodepth',
                'msg': 'Total I/O to generate at a time',
                'type': int,
                'default': 1,
            },
            {
                'name': 'reps',
                'msg': 'Number of times to repeat',
                'type': int,
                'default': 1,
            },
            {
                'name': 'nprocs',
                'msg': 'Number of threads/processes',
                'type': int,
                'default': 1,
            },
            {
                'name': 'out',
                'msg': 'Path to the output file',
                'type': str,
                'default': '/tmp/ior.bin',
            },
            {
                'name': 'direct',
                'msg': 'Use direct I/O',
                'type': bool,
                'default': False,
            },
            {
                'name': 'random',
                'msg': 'Use random I/O',
                'type': bool,
                'default': False,
            },
            {
                'name': 'engine',
                'msg': 'backend engine',
                'type': bool,
                'default': 'psync',
            },
            {
                'name': 'log',
                'msg': 'Path to IOR output log',
                'type': str,
                'default': None,
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
        # Read/write
        if self.config['read'] and self.config['write']:
            mode = 'readwrite'
        elif self.config['read']:
            mode = 'read'
        elif self.config['write']:
            mode = 'write'
        # Direct I/O
        if self.config['direct']:
            direct = 1
        else:
            direct = 0
        # Random I/O
        if self.config['random']:
            random = 1
        else:
            random = 0
        cmd = [
            'fio',
            f'--rw={mode}',
            f'--size={self.config["total_size"]}',
            f'--bs={self.config["xfer"]}',
            f'--iodepth={self.config["iodepth"]}',
            f'--numjobs={self.config["nprocs"]}',
            f'--direct={direct}',
            f'--randrepeat={random}',
            f'--filename={self.config["out"]}',
            f'--ioengine={self.config["engine"]}',
            f'--name=job',
        ]
        # The path
        if '.' in os.path.basename(self.config['out']):
            os.makedirs(str(pathlib.Path(self.config['out']).parent),
                        exist_ok=True)
        else:
            os.makedirs(self.config['out'], exist_ok=True)
        # pipe_stdout=self.config['log'] 
        Exec(' '.join(cmd),
             LocalExecInfo(env=self.mod_env,
                         hostfile=self.hostfile)).run()
        
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
        Rm(self.config['out'] + '*',
           LocalExecInfo()).run()

    def _get_stat(self, stat_dict):
        """
        Get statistics from the application.

        :param stat_dict: A dictionary of statistics.
        :return: None
        """
        stat_dict[f'{self.pkg_id}.runtime'] = self.start_time
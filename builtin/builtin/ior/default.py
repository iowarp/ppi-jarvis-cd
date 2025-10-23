"""
This module provides classes and methods to launch the Ior application.
Ior is a benchmark tool for measuring the performance of I/O systems.
It is a simple tool that can be used to measure the performance of a file system.
It is mainly targeted for HPC systems and parallel I/O.
"""
from jarvis_cd.core.pkg import Application
from jarvis_cd.shell import Exec, LocalExecInfo, MpiExecInfo, PsshExecInfo, Rm, Mkdir
from jarvis_cd.shell.process import GdbServer
from jarvis_cd.util import Hostfile
import os
import pathlib


class IorDefault(Application):
    """
    This class provides methods to launch the Ior application using default deployment.
    """
    def _init(self):
        """
        Initialize paths
        """
        pass

    def _configure(self, **kwargs):
        """
        Converts the Jarvis configuration to application-specific configuration.
        E.g., OrangeFS produces an orangefs.xml file.

        :param kwargs: Configuration parameters for this pkg.
        :return: None
        """
        # Call parent configuration (handles interceptors)
        super()._configure(**kwargs)

        self.config['api'] = self.config['api'].upper()

        # Create parent directory of output file on all nodes
        out = os.path.expandvars(self.config['out'])
        parent_dir = str(pathlib.Path(out).parent)
        Mkdir(parent_dir,
              PsshExecInfo(env=self.mod_env,
                           hostfile=self.hostfile)).run()

    def start(self):
        """
        Launch an application. E.g., OrangeFS will launch the servers, clients,
        and metadata services on all necessary pkgs.

        :return: None
        """
        cmd = [
            'ior',
            '-k',
            f'-b {self.config["block"]}',
            f'-t {self.config["xfer"]}',
            f'-a {self.config["api"]}',
            f'-o {self.config["out"]}',
        ]
        if self.config['write']:
            cmd.append('-w')
        if self.config['read']:
            cmd.append('-r')
        if self.config['fpp']:
            cmd.append('-F')
        if self.config['reps'] > 1:
            cmd.append(f'-i {self.config["reps"]}')
        if self.config['direct']:
            cmd.append('-O useO_DIRECT=1')
            
        # Build IOR command
        ior_cmd = ' '.join(cmd)

        # Use GdbServer to create gdbserver command if debugging is enabled
        gdb_server = GdbServer(ior_cmd, self.config.get('dbg_port', 4000))
        gdbserver_cmd = gdb_server.get_cmd()

        # Use multi-command format with gdbserver
        cmd_list = [
            {
                'cmd': gdbserver_cmd,
                'nprocs': 1 if self.config.get('do_dbg', False) else 0,
                'disable_preload': True
            },
            {
                'cmd': ior_cmd,
                'nprocs': None  # Will be calculated from remainder
            }
        ]
        print(cmd_list)

        Exec(cmd_list,
             MpiExecInfo(env=self.mod_env,
                         hostfile=self.hostfile,
                         nprocs=self.config['nprocs'],
                         ppn=self.config['ppn'])).run()

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
           PsshExecInfo(env=self.env,
                        hostfile=self.hostfile)).run()

    def _get_stat(self, stat_dict):
        """
        Get statistics from the application.

        :param stat_dict: A dictionary of statistics.
        :return: None
        """
        stat_dict[f'{self.pkg_id}.runtime'] = self.start_time
        
    def log(self, message):
        """
        Simple logging method
        """
        print(f"[IOR:{self.pkg_id}] {message}")
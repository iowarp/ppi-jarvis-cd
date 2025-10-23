"""
This module provides classes and methods to launch Redis.
Redis cluster is used if the hostfile has many hosts
"""
from jarvis_cd.core.pkg import Application
from jarvis_cd.shell import Exec, PsshExecInfo
from jarvis_cd.shell.process import Kill, Rm


class Filebench(Application):
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
                'name': 'workload',
                'msg': 'The filebench workload to use',
                'type': str,
                'default': 'fileserver',
                'choices': [],
                'args': [],
            },
            {
                'name': 'dir',
                'msg': 'Directory to use',
                'type': str,
                'default': '/tmp/${USER}/',
                'choices': [],
                'args': [],
            },
            {
                'name': 'run',
                'msg': 'Total runtime (seconds)',
                'type': int,
                'default': 15,
                'choices': [],
                'args': [],
            },
        ]

    def _configure(self, **kwargs):
        """
        Converts the Jarvis configuration to application-specific configuration.
        E.g., OrangeFS produces an orangefs.xml file.

        :param kwargs: Configuration parameters for this pkg.
        :return: None
        """
        # Create the redis hostfile
        workload = self.config['workload']
        dir = os.path.expandvars(self.config['dir'])
        nfiles = SizeConv.to_int(self.config['nfiles'])
        self.copy_template_file(f'{self.pkg_dir}/config/{workload}.f',
                                f'{self.shared_dir}/{workload}.f',
                                {
                                    'DIR': dir,
                                    'RUN': self.config['run'],
                                })

    def start(self):
        """
        Launch an application. E.g., OrangeFS will launch the servers, clients,
        and metadata services on all necessary pkgs.

        :return: None
        """
        cmd = [
            'setarch `arch` --addr-no-randomize',
            'filebench',
            f'-f {self.shared_dir}/{self.config["workload"]}.f',
        ]
        cmd = ' '.join(cmd)
        self.log(cmd, color=Color.YELLOW)
        Exec(cmd,
             PsshExecInfo(env=self.mod_env,
                          hostfile=self.hostfile)).run()

    def stop(self):
        """
        Stop a running application. E.g., OrangeFS will terminate the servers,
        clients, and metadata services.

        :return: None
        """
        Kill('filebench',
             PsshExecInfo(env=self.env,
                          hostfile=self.hostfile)).run()

    def clean(self):
        """
        Destroy all data for an application. E.g., OrangeFS will delete all
        metadata and data directories in addition to the orangefs.xml file.

        :return: None
        """
        Rm(self.config['dir'] + '*',
           PsshExecInfo(env=self.env,
                        hostfile=self.hostfile)).run()

"""
This module provides classes and methods to launch the SparkCluster service.
SparkCluster is ....
"""

from jarvis_cd.core.pkg import Service
from jarvis_cd.shell import Exec, PsshExecInfo


class SparkCluster(Service):
    """
    This class provides methods to launch the SparkCluster service.
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
                'name': 'port',
                'msg': '',
                'type': int,
                'default': 7077,
            },
            {
                'name': 'num_nodes',
                'msg': '',
                'type': int,
                'default': 1,
            },
        ]

    def _configure(self, **kwargs):
        """
        Converts the Jarvis configuration to application-specific configuration.
        E.g., OrangeFS produces an orangefs.xml file.

        :param kwargs: Configuration parameters for this pkg.
        :return: None
        """
        self.config['SPARK_SCRIPTS'] = self.env['SPARK_SCRIPTS']
        self.env['SPARK_MASTER_HOST'] = self.hostfile.hosts[0]
        self.env['SPARK_MASTER_PORT'] = '7077'
        self.env['SPARK_WORKER_PORT'] = '7078'

    def start(self):
        """
        Launch an application. E.g., OrangeFS will launch the servers, clients,
        and metadata services on all necessary pkgs.

        :return: None
        """
        # Start the master node
        Exec(f'{self.config["SPARK_SCRIPTS"]}/sbin/start-master.sh',
             PsshExecInfo(env=self.env,
                          hosts=self.hostfile.subset(1))).run()
        time.sleep(1)
        # Start the worker nodes
        Exec(f'{self.config["SPARK_SCRIPTS"]}/sbin/start-worker.sh '
             f'{self.env["SPARK_MASTER_HOST"]}:{self.env["SPARK_MASTER_PORT"]}',
             PsshExecInfo(env=self.mod_env,
                          hosts=self.hostfile.subset(self.config['num_nodes']))).run()
        time.sleep(self.config['sleep'])

    def stop(self):
        """
        Stop a running application. E.g., OrangeFS will terminate the servers,
        clients, and metadata services.

        :return: None
        """
        # Start the master node
        Exec(f'{self.config["SPARK_SCRIPTS"]}/sbin/stop-master.sh',
             PsshExecInfo(env=self.env,
                          hosts=self.hostfile.subset(1))).run()
        # Start the worker nodes
        Exec(f'{self.config["SPARK_SCRIPTS"]}/sbin/stop-worker.sh '
             f'{self.env["SPARK_MASTER_HOST"]}',
             PsshExecInfo(env=self.env,
                          hosts=self.hostfile)).run()

    def clean(self):
        """
        Destroy all data for an application. E.g., OrangeFS will delete all
        metadata and data directories in addition to the orangefs.xml file.

        :return: None
        """
        pass

    def status(self):
        """
        Check whether or not an application is running. E.g., are OrangeFS
        servers running?

        :return: True or false
        """
        return True

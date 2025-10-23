"""
This module provides classes and methods to launch the Cm1 application.
Cm1 is ....
"""
from jarvis_cd.core.pkg import Application
from jarvis_cd.shell import Exec, LocalExecInfo, MpiExecInfo
from jarvis_cd.shell.process import Mkdir


class Cm1(Application):
    """
    This class provides methods to launch the Cm1 application.
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
                'name': 'nx',
                'msg': 'x dimension of 3-D grid',
                'type': int,
                'default': 16,
            },
            {
                'name': 'ny',
                'msg': 'y dimension of 3-D grid',
                'type': int,
                'default': 16,
            },
            {
                'name': 'nz',
                'msg': 'z dimension of 3-D grid',
                'type': int,
                'default': 16,
            },
            {
                'name': 'corex',
                'msg': 'Number of cores for x dimension',
                'type': int,
                'default': 2,
            },
            {
                'name': 'corey',
                'msg': 'Number of cores for x dimension',
                'type': int,
                'default': 2,
            },
            {
                'name': 'file_type',
                'msg': 'The file type to use',
                'type': str,
                'choices': ['grads', 'netcdf', 'lofs'],
                'default': 'netcdf',
            },
            {
                'name': 'file_count',
                'msg': 'The number of files to generate',
                'type': str,
                'choices': ['shared', 'fpo', 'fpp', 'lofs'],
                'default': 'shared',
            },
            {
                'name': 'TEST_CASE',
                'msg': 'The test to run',
                'type': str,
                'choices': ['nssl3'],
                'default': None,
            },
            {
                'name': 'ppn',
                'msg': 'The number of processes per node',
                'type': int,
                'default': 1,
            },
            {
                'name': 'output',
                'msg': 'The directory to output data to',
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
        # Create output directories
        if self.config['output'] is None:
            self.config['output'] = f'{self.shared_dir}/cm1_out'
        out_parent = str(pathlib.Path(self.config['output']).parent)
        self.config['restart'] = os.path.join(out_parent, 'restart_dir')
        Mkdir([self.config['output'], self.config['restart']],
              LocalExecInfo()).run()

        # Create CM1 compilation
        self.config['CM1_PATH'] = self.env['CM1_PATH']
        Exec(f'bash {self.config["CM1_PATH"]}/buildCM1-spack.sh',
             LocalExecInfo(env=self.env)).run()

        # Create CM1 configuration
        self.env['COREX'] = self.config['corex']
        self.env['COREY'] = self.config['corey']
        corex = self.config['corex']
        corey = self.config['corey']
        namelist_in = os.path.join(self.pkg_dir, 'config',
                                   'namelist.input.nssl3')
        namelist_out = os.path.join(self.shared_dir, 'namelist.input.nssl3')
        if self.config['file_format'] == 'grads':
            file_format = 1
        elif self.config['file_format'] == 'netcdf':
            file_format = 2
        elif self.config['file_format'] == 'lofs':
            file_format = 5
        else:
            raise Exception("Invalid file format")

        if self.config['file_count'] == 'shared':
            file_count = 1
        elif self.config['file_count'] == 'fpo':
            file_count = 2
        elif self.config['file_count'] == 'fpp':
            file_count = 3
        elif self.config['file_count'] == 'lofs':
            file_count = 4
        else:
            raise Exception("Invalid file count")

        self.copy_template_file(namelist_in, namelist_out, replacements=[
            ('file_format', file_format),
            ('file_count', file_count),
            ('nx', self.config['nx']),
            ('ny', self.config['ny']),
            ('nz', self.config['nz']),
            ('nodex', corex),
            ('nodey', corey),
            ('rankx', corex),
            ('ranky', corey),
            ('ppn', self.config['ppn']),
        ])

    def start(self):
        """
        Launch an application. E.g., OrangeFS will launch the servers, clients,
        and metadata services on all necessary pkgs.

        :return: None
        """
        cmd = [
            f'{self.config["CM1_PATH"]}/run/cm1.exe',
            self.config['namelist'],
            self.config['output'],
            'cm1_data',
            self.config['restart']
        ]
        cmd = ' '.join(cmd)
        corex = self.config['corex']
        corey = self.config['corey']
        Exec(cmd, MpiExecInfo(env=self.env,
                              nprocs=corex * corey,
                              ppn=self.config['ppn'],
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
        pass

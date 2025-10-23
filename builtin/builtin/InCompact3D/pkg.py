"""
This module provides classes and methods to launch the Incompact3d application.
Incompact3d is ....
"""
from jarvis_cd.core.pkg import Application
from jarvis_cd.shell import Exec, MpiExecInfo, PsshExecInfo
from jarvis_cd.shell.process import Rm
import os

class Incompact3d(Application):
    """
    This class provides methods to launch the Incompact3d application.
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
                'name': 'output_folder',
                'msg': 'The location of incompact3D',
                'type': str,
                'default': None,
            },
            {
                'name': 'engine',
                'msg': 'Engine to be used',
                'choices': ['bp5', 'hermes'],
                'type': str,
                'default': 'bp5',
            },
            {
                'name': 'Incompact3D_location',
                'msg': 'The location of incompact3D',
                'type': str,
                'default': None,
            },
            {
                'name': 'benchmarks',
                'msg': 'The name of benchmarks ',
                'choices': ['ABL-Atmospheric-Boundary-Layer', 'Channel', 'Cylinder-wake', 'Mixing-layer', 'Pipe-Flow',
                            'TBL-Turbulent-Boundary-Layer', 'Gravity-current',  'Particle-Tracking', 'Sandbox', 'TGV-Taylor-Green-vortex',
                            'Cavity', 'MHD', 'Periodic-hill', 'Sphere',  'Wind-Turbine'],
                'type': str,
                'default': 'Cavity',
            },
            {
                'name': 'script_file_name',
                'msg': 'The name of script file',
                'type': str,
                'default': None,
            },
            {
                'name': 'db_path',
                'msg': 'Path where the DB will be stored',
                'type': str,
                'default': 'benchmark_metadata.db',
            },
            {
                'name': 'output_location',
                'msg': 'Path where the output file will be stored',
                'type': str,
                'default': 'data.bp5',
            },
            {
                'name': 'logs',
                'msg': 'Path where the log file will be stored',
                'type': str,
                'default': 'logs.txt',
            },

        ]

    def _configure(self, **kwargs):
        """
        Converts the Jarvis configuration to application-specific configuration.
        E.g., OrangeFS produces an orangefs.xml file.

        :param kwargs: Configuration parameters for this pkg.
        :return: None
        """
        execute_location = os.path.join(
            self.config['output_folder'],
            'examples',
            self.config['benchmarks']
        )

# Explicitly check if the directory exists, then create it
        if not os.path.exists(execute_location):
            os.makedirs(execute_location)
        if self.config['engine'].lower() == 'bp5':
            self.copy_template_file(f'{self.pkg_dir}/config/adios2.xml',
                                    f'{execute_location}/adios2_config.xml')
        if self.config['engine'].lower() in ['hermes', 'hermes_derived']:
            self.copy_template_file(f'{self.pkg_dir}/config/hermes.xml',
                                    f'{execute_location}/adios2_config.xml', replacements={
                    'ppn': self.config['ppn'],
                    'db_path': self.config['db_path'],
                })
        input_i3d = f"{self.config['Incompact3D_location']}/examples/{self.config['benchmarks']}/{self.config['script_file_name']}"
        self.copy_template_file(f'{input_i3d}',
                                f'{execute_location}/input.i3d')
        pass

    def start(self):
        """
        Launch an application. E.g., OrangeFS will launch the servers, clients,
        and metadata services on all necessary pkgs.

        :return: None
        """

        execute_location=self.config['output_folder']+ '/examples/' + self.config['benchmarks']
        Exec('xcompact3d',
             MpiExecInfo(nprocs=self.config['nprocs'],
                         ppn=self.config['ppn'],
                         hostfile=self.hostfile,
                         env=self.mod_env,
                         cwd=execute_location
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
        output_file= self.config['incompact3D_location']+ '/examples/' + self.config['benchmarks'] +'/data.bp5'
        output_files = [output_file,
                       self.config['checkpoint_output'],
                       self.config['db_path']
                       ]

        print(f'Removing {output_files}')
        Rm(output_files, PsshExecInfo(hostfile=self.hostfile)).run()
        pass
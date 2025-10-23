"""
This module provides classes and methods to launch the Gray Scott application.
Gray Scott is a 3D 7-point stencil code for modeling the diffusion of two
substances.
"""
from jarvis_cd.core.pkg import Application, Color
from jarvis_cd.shell import Exec, MpiExecInfo, PsshExecInfo
from jarvis_cd.shell.process import Mkdir, Rm
import time
import pathlib


class GrayScott(Application):
    """
    This class provides methods to launch the GrayScott application.
    """
    def _init(self):
        """
        Initialize paths
        """
        self.adios2_xml_path = f'{self.shared_dir}/adios2.xml'
        self.settings_json_path = f'{self.shared_dir}/settings-files.json'

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
                'msg': 'Number of processes to spawn',
                'type': int,
                'default': 4,
            },
            {
                'name': 'ppn',
                'msg': 'Processes per node',
                'type': int,
                'default': None,
            },
            {
                'name': 'L',
                'msg': 'Grid size of cube',
                'type': int,
                'default': 32,
            },
            {
                'name': 'Du',
                'msg': 'Diffusion rate of substance U',
                'type': float,
                'default': .2,
            },
            {
                'name': 'Dv',
                'msg': 'Diffusion rate of substance V',
                'type': float,
                'default': .1,
            },
            {
                'name': 'F',
                'msg': 'Feed rate of U',
                'type': float,
                'default': .01,
            },
            {
                'name': 'k',
                'msg': 'Kill rate of V',
                'type': float,
                'default': .05,
            },
            {
                'name': 'dt',
                'msg': 'Timestep',
                'type': float,
                'default': 2.0,
            },
            {
                'name': 'steps',
                'msg': 'Total number of steps to simulate',
                'type': int,
                'default': 100,
            },
            {
                'name': 'plotgap',
                'msg': 'Number of steps between output',
                'type': float,
                'default': 10,
            },
            {
                'name': 'noise',
                'msg': 'Amount of noise',
                'type': float,
                'default': .01,
            },
            {
                'name': 'output',
                'msg': 'Absolute path to output data',
                'type': str,
                'default': None,
            },
            {
                'name': 'engine',
                'msg': 'Engien to be used',
                'choices': ['bp5', 'hermes'],
                'type': str,
                'default': 'bp5',
            },
        ]

    def _configure(self, **kwargs):
        """
        Converts the Jarvis configuration to application-specific configuration.
        E.g., OrangeFS produces an orangefs.xml file.

        :param kwargs: Configuration parameters for this pkg.
        :return: None
        """
        if self.config['output'] is None:
            adios_dir = os.path.join(self.shared_dir, 'gray-scott-output')
            self.config['output'] = os.path.join(adios_dir,
                                                 'data')
            Mkdir(adios_dir, PsshExecInfo(hostfile=self.hostfile,
                                          env=self.env)).run()
        settings_json = {
            'L': self.config['L'],
            'Du': self.config['Du'],
            'Dv': self.config['Dv'],
            'F': self.config['F'],
            'k': self.config['k'],
            'dt': self.config['dt'],
            'plotgap': self.config['plotgap'],
            'steps': self.config['steps'],
            'noise': self.config['noise'],
            'output': f'{self.config["output"]}',
            'adios_config': self.adios2_xml_path
        }
        Mkdir(self.config['output'],
              PsshExecInfo(hostfile=self.hostfile,
                           env=self.env)).run()
        JsonFile(self.settings_json_path).save(settings_json)

        if self.config['engine'].lower() == 'bp5':
            self.copy_template_file(f'{self.pkg_dir}/config/adios2.xml',
                                self.adios2_xml_path)
        elif self.config['engine'].lower() == 'hermes':
            self.copy_template_file(f'{self.pkg_dir}/config/hermes.xml',
                                    self.adios2_xml_path)
        else:
            raise Exception('Engine not defined')

    def start(self):
        """
        Launch an application. E.g., OrangeFS will launch the servers, clients,
        and metadata services on all necessary pkgs.

        :return: None
        """
        # print(self.env['HERMES_CLIENT_CONF'])
        start = time.time()
        Exec(f'gray-scott {self.settings_json_path}',
             MpiExecInfo(nprocs=self.config['nprocs'],
                         ppn=self.config['ppn'],
                         hostfile=self.hostfile,
                         env=self.mod_env)).run()
        end = time.time()
        diff = end - start
        self.log(f'TIME: {diff} seconds', color=Color.GREEN)

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
        output_dir = self.config['output'] + "*"
        print(f'Removing {output_dir}')
        Rm(output_dir).run()
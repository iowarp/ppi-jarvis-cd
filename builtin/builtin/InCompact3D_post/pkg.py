"""
This module provides classes and methods to launch the Incompact3dPost application.
Incompact3dPost is ....
"""
from jarvis_cd.core.pkg import Application
from jarvis_cd.shell import Exec


class Incompact3dPost(Application):
    """
    This class provides methods to launch the Incompact3dPost application.
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
                'default': None,
            },
            {
                'name': 'engine',
                'msg': 'Engine to be used',
                'type': str,
                'default': 'bp5',
            },
            {
                'name': 'db_path',
                'msg': 'Path where the DB will be stored',
                'type': str,
                'default': 'benchmark_metadata.db',
            },
            {
                'name': 'in_filename',
                'msg': 'Input file location',
                'type': str,
                'default': 'data.bp5',
            },
            {
                'name': 'output_folder',
                'msg': 'Input file location',
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
                'name': 'out_filename',
                'msg': 'Output file location',
                'type': str,
                'default': 'out.bp5',
            },
            {
                'name': 'derived_variable_type',
                'msg': 'the type of derived variable in simulation',
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
        execute_location = os.path.join(
            self.config['output_folder'],
            'examples',
            self.config['benchmarks']
        )
        if self.config['engine'].lower() == 'bp5':
            self.copy_template_file(f'{self.pkg_dir}/config/adios2.xml',
                                    f'{execute_location}/adios2_config.xml')
        if self.config['engine'].lower() in ['hermes', 'hermes_derived']:
            self.copy_template_file(f'{self.pkg_dir}/config/hermes.xml',
                                    f'{execute_location}/adios2_config.xml', replacements={
                    'ppn': self.config['ppn'],
                    'db_path': self.config['db_path'],
                })
        pass

    def start(self):
        """
        Launch an application. E.g., OrangeFS will launch the servers, clients,
        and metadata services on all necessary pkgs.

        :return: None
        """
        in_file = self.config['in_filename']
        out_file = self.config['out_filename']
        execute_location=self.config['output_folder']+ '/examples/' + self.config['benchmarks']
        # Exec(f'inCompact3D_analysis {in_file} {out_file}',
        #      MpiExecInfo(nprocs=self.config['nprocs'],
        #                  ppn=self.config['ppn'],
        #                  hostfile=self.hostfile,
        #                  env=self.mod_env,
        #                  cwd=execute_location
        #                  ))
        os.chdir(execute_location)
        Exec(f'inCompact3D_analysis {in_file} {out_file}').run()
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
        output_dir = [self.config['in_filename'],
                      self.config['out_filename'],
                      self.config['db_path']
                      ]
        print(f'Removing {output_dir}')
        Rm(output_dir, PsshExecInfo(hostfile=self.hostfile)).run()
        pass
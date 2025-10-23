"""
This module provides classes and methods to launch the Gadget2 application.
Gadget2 is ....
"""
from jarvis_cd.core.pkg import Application
from jarvis_cd.shell import Exec, LocalExecInfo, MpiExecInfo
from jarvis_cd.shell.process import Mkdir, Rm


class Gadget2(Application):
    """
    This class provides methods to launch the Gadget2 application.
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
                'msg': 'Number of processes to spawn',
                'type': int,
                'default': 1,
            },
            {
                'name': 'ppn',
                'msg': 'Processes per node',
                'type': int,
                'default': None,
            },
            {
                'name': 'j',
                'msg': 'Number of threads to use for building gadget',
                'type': int,
                'default': 8,
            },
            {
                'name': 'test_case',
                'msg': 'The test case to use',
                'type': str,
                'default': 'gassphere',
            },
            {
                'name': 'out',
                'msg': 'The directory to output data to',
                'type': str,
                'default': '${HOME}/gadget_data',
            },
            {
                'name': 'buffer_size',
                'msg': 'The size in MB of buffers used for communication. '
                       '100MB is typically an upper bound.',
                'type': float,
                'default': 15,
            },
            {
                'name': 'part_alloc_factor',
                'msg': 'Allocate space for particles per processor. '
                       'Typically should be in the range of 1 to 3.',
                'type': float,
                'default': 1.1,
            },
            {
                'name': 'tree_alloc_factor',
                'msg': 'Allocate space for the BH-tree, which is typically '
                       'smaller than the number of particles.',
                'type': float,
                'default': .9,
            },
            {
                'name': 'max_size_timestep',
                'msg': 'The maximum time step of a particle',
                'type': float,
                'default': .01,
            },
            {
                'name': 'time_max',
                'msg': 'The maximum time the simulation estimates (seconds)',
                'type': float,
                'default': 3,
            },
            {
                'name': 'time_bet_snapshot',
                'msg': 'The number of estimated seconds before snapshot occurs',
                'type': float,
                'default': .2,
            },
            {
                'name': 'ic',
                'msg': 'The initial conditions file to use.',
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
        test_case = self.config['test_case']
        paramfile = f'{self.config_dir}/{test_case}.param'
        buildconf = f'{self.pkg_dir}/config/{test_case}.yaml'
        outdir = expand_env(self.config['out'])
        self.copy_template_file(f'{self.pkg_dir}/paramfiles/{test_case}.param',
                                paramfile,
                                replacements={
                                    'OUTPUT_DIR': outdir,
                                    'REPO_DIR': self.env['GADGET2_PATH'],
                                    'BUFFER_SIZE': self.config['buffer_size'],
                                    'PART_ALLOC_FACTOR': self.config['part_alloc_factor'],
                                    'TREE_ALLOC_FACTOR': self.config['tree_alloc_factor'],
                                    'TIME_MAX': self.config['time_max'],
                                    'TIME_BET_SNAPSHOT': self.config['time_bet_snapshot'],
                                    'MAX_SIZE_TIMESTEP': self.config['max_size_timestep'],
                                    'INITCOND': self.config['ic'],
                                })
        build_dir = f'{self.shared_dir}/build'
        cmake_opts = YamlFile(buildconf).load()
        if 'FFTW_PATH' in self.env:
            cmake_opts['FFTW_PATH'] = self.env['FFTW_PATH']
        Cmake(self.env['GADGET2_PATH'],
              build_dir,
              opts=cmake_opts,
              exec_info=LocalExecInfo(env=self.env))
        Make(build_dir, nthreads=self.config['j'],
             exec_info=LocalExecInfo(env=self.env))

    def start(self):
        """
        Launch an application. E.g., OrangeFS will launch the servers, clients,
        and metadata services on all necessary pkgs.

        :return: None
        """
        test_case = self.config['test_case']
        build_dir = f'{self.shared_dir}/build'
        exec_path = f'{build_dir}/bin/Gadget2'
        paramfile = f'{self.config_dir}/{test_case}.param'
        Mkdir(self.config['out']).run()
        Exec(f'{exec_path} {paramfile}',
             MpiExecInfo(nprocs=self.config['nprocs'],
                         ppn=self.config['ppn'],
                         hostfile=self.hostfile,
                         env=self.mod_env,
                         cwd=self.env['GADGET2_PATH'])).run()

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
        build_dir = f'{self.shared_dir}/build'
        Rm([self.config['out']]).run()

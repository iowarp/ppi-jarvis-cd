"""
This module provides classes and methods to launch the Ior application.
Ior is a benchmark tool for measuring the performance of I/O systems.
It is a simple tool that can be used to measure the performance of a file system.
It is mainly targeted for HPC systems and parallel I/O.
"""
from jarvis_cd.core.route_pkg import RouteApp


class Ior(RouteApp):
    """
    Router class for IOR deployment - delegates to default or container implementation.
    """

    def _configure_menu(self):
        """
        Create a CLI menu for the configurator method.

        :return: List(dict)
        """
        # Get base menu from RouteApp (includes deploy_mode)
        base_menu = super()._configure_menu()

        # Override deploy_mode choices to show available deployment modes
        for item in base_menu:
            if item['name'] == 'deploy_mode':
                item['choices'] = ['default', 'container']
                break

        # Add all IOR parameters (shared by both default and container deployments)
        ior_menu = [
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
                'name': 'block',
                'msg': 'Amount of data to generate per-process',
                'type': str,
                'default': '32m',
                'aliases': ['block_size']
            },
            {
                'name': 'api',
                'msg': 'The I/O api to use',
                'type': str,
                'choices': ['posix', 'mpiio', 'hdf5'],
                'default': 'posix',
            },
            {
                'name': 'fpp',
                'msg': 'Use file-per-process',
                'type': bool,
                'default': False,
            },
            {
                'name': 'reps',
                'msg': 'Number of times to repeat',
                'type': int,
                'default': 1,
            },
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
                'name': 'out',
                'msg': 'Path to the output file',
                'type': str,
                'default': '/tmp/ior.bin',
                'aliases': ['output']
            },
            {
                'name': 'log',
                'msg': 'Path to IOR output log',
                'type': str,
                'default': '',
            },
            {
                'name': 'direct',
                'msg': 'Use direct I/O (O_DIRECT) for POSIX API, bypassing I/O buffers',
                'type': bool,
                'default': False,
            }
        ]

        # Combine base menu with IOR-specific menu
        return base_menu + ior_menu
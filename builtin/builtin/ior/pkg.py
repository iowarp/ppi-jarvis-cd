"""
This module provides classes and methods to launch the Ior application.
Ior is a benchmark tool for measuring the performance of I/O systems.
It is a simple tool that can be used to measure the performance of a file system.
It is mainly targeted for HPC systems and parallel I/O.
"""
from jarvis_cd.core.pkg import Application


class Ior(Application):
    """
    Router class for IOR deployment - delegates to default or container implementation.
    """

    def __new__(cls, pipeline=None):
        """
        Factory method to create the appropriate IOR implementation based on deploy parameter.

        :param pipeline: Pipeline instance
        :return: IorDefault or IorContainer instance
        """
        # If we're being called with a specific subclass, use normal instantiation
        if cls is not Ior:
            instance = super(Application, cls).__new__(cls)
            return instance

        # For the base Ior class, we need to determine which implementation to use
        # However, at __new__ time we don't have access to the config yet
        # So we'll use normal instantiation and handle routing in __init__
        instance = super(Application, cls).__new__(cls)
        return instance

    def __init__(self, pipeline=None):
        """
        Initialize the router and delegate to appropriate implementation.

        :param pipeline: Pipeline instance
        """
        # Check if this is already a delegated instance
        if self.__class__ is not Ior:
            super().__init__(pipeline=pipeline)
            return

        # Store pipeline temporarily to access config
        self._temp_pipeline = pipeline

        # Initialize with default implementation first
        super().__init__(pipeline=pipeline)

        # Now check config to determine if we should delegate
        # This will be set during configure
        self._delegate = None

    def _init(self):
        """Initialize paths"""
        pass

    def _configure_menu(self):
        """
        Create a CLI menu for the configurator method.

        :return: List(dict)
        """
        # Get base menu from Application (includes interceptors)
        base_menu = super()._configure_menu()

        # Add all IOR parameters (shared by both default and container deployments)
        ior_menu = [
            {
                'name': 'deploy',
                'msg': 'Deployment method for IOR',
                'type': str,
                'choices': ['default', 'podman', 'docker'],
                'default': 'default',
            },
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
                'default': None,
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

    def _configure(self, **kwargs):
        """
        Configure the appropriate implementation.

        :param kwargs: Configuration parameters
        :return: None
        """
        # Call parent to set config
        super()._configure(**kwargs)

        # Determine deploy mode (map docker/podman to container)
        deploy_mode = self.config.get('deploy', 'default')
        if deploy_mode in ['docker', 'podman']:
            deploy_mode = 'container'

        # Delegate to appropriate implementation
        delegate = self._get_delegate(deploy_mode)
        delegate._configure(**kwargs)

    def start(self):
        """
        Start IOR using the appropriate implementation.

        :return: None
        """
        # Determine deploy mode (map docker/podman to container)
        deploy_mode = self.config.get('deploy', 'default')
        if deploy_mode in ['docker', 'podman']:
            deploy_mode = 'container'

        delegate = self._get_delegate(deploy_mode)
        delegate.start()

    def stop(self):
        """
        Stop IOR using the appropriate implementation.

        :return: None
        """
        # Determine deploy mode (map docker/podman to container)
        deploy_mode = self.config.get('deploy', 'default')
        if deploy_mode in ['docker', 'podman']:
            deploy_mode = 'container'

        delegate = self._get_delegate(deploy_mode)
        delegate.stop()

    def clean(self):
        """
        Clean IOR data using the appropriate implementation.

        :return: None
        """
        # Determine deploy mode (map docker/podman to container)
        deploy_mode = self.config.get('deploy', 'default')
        if deploy_mode in ['docker', 'podman']:
            deploy_mode = 'container'

        delegate = self._get_delegate(deploy_mode)
        delegate.clean()
"""
This module provides classes and methods to inject the Asan interceptor.
Asan is a library to detect memory errors.
"""
from jarvis_cd.core.pkg import Interceptor


class Asan(Interceptor):
    """
    This class provides methods to inject the Asan interceptor.
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
        return []

    def _configure(self, **kwargs):
        """
        Converts the Jarvis configuration to application-specific configuration.
        E.g., OrangeFS produces an orangefs.xml file.

        :param kwargs: Configuration parameters for this pkg.
        :return: None
        """
        self.config['LIBASAN'] = self.find_library('asan')
        if self.config['LIBASAN'] is None:
            raise Exception('Could not find libasan')
        print(f'Found libasan.so at {self.config["LIBASAN"]}')

    def modify_env(self):
        """
        Modify the jarvis environment.

        :return: None
        """
        self.prepend_env('LD_PRELOAD', self.config['LIBASAN'])

"""
This module provides classes and methods to launch the DataStagein application.
DataStagein is ....
"""
from jarvis_cd.core.pkg import Application
import os
import pathlib
import time


class CosmicTagger(Application):
    """
    This class provides methods to launch the DataStagein application.
    """
    def _init(self):
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
                'name': 'train_file',
                'msg': 'Train filename (not abspath)',
                'type': str,
                'default': 'cosmic_tagging_light.h5',
            },
            {
                'name': 'test_file',
                'msg': 'Test filename (not abspath)',
                'type': str,
                'default': 'cosmic_tagging_test.h5',
            },
            {
                'name': 'dataset_dir',
                'msg': 'Dataset directory (abspath)',
                'type': str,
                'default': '/home/llogan/Documents/Apps/CosmicTagger/example_data/',
            },
        ]
            
    def _configure(self, **kwargs):
        """
        Converts the Jarvis configuration to application-specific configuration.
        E.g., OrangeFS produces an orangefs.xml file.

        :param kwargs: Configuration parameters for this pkg.
        :return: None
        """
        src_path = f'{self.pkg_dir}/config/config.yaml'
        dst_path = f'{self.env["TAGGER_ROOT"]}/src/config/config.yaml'
        self.copy_template_file(src_path, dst_path, replacements= {
            'TRAIN_FILE': self.config['train_file'],
            'TEST_FILE': self.config['test_file'],
            'DATASET_DIR': self.config['dataset_dir'],
        })
        self.log(dst_path, Color.YELLOW)
    
    def start(self):
        """
        Launch an application. E.g., OrangeFS will launch the servers, clients,
        and metadata services on all necessary pkgs.

        :return: None
        """
        # Exec('conda ')

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

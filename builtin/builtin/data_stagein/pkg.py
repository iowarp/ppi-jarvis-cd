"""
This module provides classes and methods to launch the DataStagein application.
DataStagein is ....
"""
from jarvis_cd.core.pkg import Application
from jarvis_cd.shell import Exec, LocalExecInfo
import os
import pathlib
import time


class DataStagein(Application):
    """
    This class provides methods to launch the DataStagein application.
    """
    def _init(self):
        """
        Initialize paths
        """
        
        # Convert user_data_paths to list
        try:
            user_data_paths = self.config['user_data_paths']
            if user_data_paths is not None:
                self.user_data_list = user_data_paths.split(',')
        except KeyError:
            self.user_data_list = []
        
        try:
            # Convert mkdir_datapaths to list
            mkdir_datapaths = self.config['mkdir_datapaths']
            if mkdir_datapaths is not None:
                self.mkdir_datapaths_list = mkdir_datapaths.split(',')
        except KeyError:
            self.mkdir_datapaths_list = []
        

    def _configure_menu(self):
        """
        Create a CLI menu for the configurator method.
        For thorough documentation of these parameters, view:
        https://github.com/scs-lab/jarvis-util/wiki/3.-Argument-Parsing

        :return: List(dict)
        """
        return [
            {
                'name': 'user_data_paths',
                'msg': 'List of paths of user datas to stage in, delimitated by comma',
                'type': str,
                'default': None,
            },
            {
                'name': 'dest_data_path',
                'msg': 'The destination path for all user datas to be staged in',
                'type': str,
                'default': None,
            },
            {
                'name': 'mkdir_datapaths',
                'msg': 'List of paths tp create if it does not exist, delimitated by comma',
                'type': str,
                'default': None,
            },
        ]
    
    def _print_required_params(self):
        required_params = ['dest_data_path', 'user_data_paths', 'mkdir_datapaths']
        print("data_stagein Required parameters: ")
        for param in required_params:
            print(f"    {param}")
            
    def _configure(self, **kwargs):
        """
        Converts the Jarvis configuration to application-specific configuration.
        E.g., OrangeFS produces an orangefs.xml file.

        :param kwargs: Configuration parameters for this pkg.
        :return: None
        """
        # Convert user_data_paths to list
        try:
            user_data_paths = self.config['user_data_paths']
            if user_data_paths is not None:
                self.user_data_list = user_data_paths.split(',')
        except KeyError:
            self.user_data_list = []
        
        try:
            # Convert mkdir_datapaths to list
            mkdir_datapaths = self.config['mkdir_datapaths']
            if mkdir_datapaths is not None:
                self.mkdir_datapaths_list = mkdir_datapaths.split(',')
        except KeyError:
            self.mkdir_datapaths_list = []

        self.log(f"user_data_list: {self.user_data_list}")
        self.log(f"mkdir_datapaths_list: {self.mkdir_datapaths_list}")
        
        if self.config['dest_data_path'] is None:
            self._print_required_params()
            raise ValueError("dest_data_path is not set")
        if self.config['user_data_paths'] is None:
            self._print_required_params()
            raise ValueError("user_data_paths is not set")
        if self.config['mkdir_datapaths'] is None:
            self._print_required_params()
            raise ValueError("mkdir_datapaths is not set")
        
        self.config['dest_data_path'] = self.config['dest_data_path']
    
    def start(self):
        """
        Launch an application. E.g., OrangeFS will launch the servers, clients,
        and metadata services on all necessary pkgs.

        :return: None
        """
        print("Data stagein starting")
        
        user_data_list = self.user_data_list
        dest_data_path = self.config['dest_data_path']
        mkdir_datapaths_list = self.mkdir_datapaths_list
        
        print(f"dest_data_path: {dest_data_path}")
        print(f"user_data_list: {user_data_list}")
        print(f"mkdir_datapaths_list: {mkdir_datapaths_list}")
        
        
        # create paths for user
        for datapath in mkdir_datapaths_list:
            if not pathlib.Path(datapath).exists():
                pathlib.Path(datapath).mkdir(parents=True, exist_ok=True)
            else:
                print(f"Path {datapath} already exists")
        
        # create destination path if it does not exist
        if not pathlib.Path(dest_data_path).exists():
            pathlib.Path(dest_data_path).mkdir(parents=True, exist_ok=True)
        
        start = time.time()
        
        for data_path in user_data_list:
            if not os.path.exists(data_path):
                raise FileNotFoundError(f"Data path {data_path} does not exist")
            else:
                # check if data_path is a directory
                if os.path.isdir(data_path):
                    # Check if the path is empty (e.g. does not contain any files)
                    if len(os.listdir(data_path)) == 0:
                        raise ValueError(f"Data path {data_path} is empty")
                else:
                    # Check if the file is not empty
                    if os.stat(data_path).st_size == 0:
                        raise ValueError(f"Data file {data_path} is empty")
            
            # Check if two directory contains the same files
            dest_files = os.listdir(dest_data_path)
            if os.path.isdir(data_path) and set(dest_files) == set(os.listdir(data_path)):
                # data_files = os.listdir(data_path)
                # if set(dest_files) == set(data_files):
                print(f"Data path {data_path} already exists in {dest_data_path}")
                continue
            
            # Move data to destination path
            cmd = f"cp -r {data_path} {dest_data_path}"
            print(f"Copying data from {data_path} to {dest_data_path}")
            Exec(cmd,LocalExecInfo(env=self.mod_env,)).run()
            
            copied_items = 1
            if os.path.isdir(data_path): copied_items = len(os.listdir(data_path))
            print(f"Copied {copied_items} items ... ")
        
        end = time.time()
        diff = end - start
        self.log(f'data_stagein TIME: {diff} seconds')
            
        print("Data stagein complete")

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

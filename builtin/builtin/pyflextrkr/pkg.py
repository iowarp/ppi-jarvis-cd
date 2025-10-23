"""
This module provides classes and methods to launch the Gray Scott application.
Pyflextrkr is ....
"""
from jarvis_cd.core.pkg import Application, Color
from jarvis_cd.shell import Exec, LocalExecInfo
import time
import pathlib

import yaml
from scspkg.pkg import Package

class Pyflextrkr(Application):
    """
    This class provides methods to launch the Pyflextrkr application.
    """
    def _init(self):
        """
        Initialize paths
        """
        self.pkg_type = 'pyflextrkr'
        self.hermes_env_vars = ['HERMES_ADAPTER_MODE', 'HERMES_CLIENT_CONF', 
                                'HERMES_CONF', 'LD_PRELOAD']

    def _configure_menu(self):
        """
        Create a CLI menu for the configurator method.
        For thorough documentation of these parameters, view:
        https://github.com/scs-lab/jarvis-util/wiki/3.-Argument-Parsing

        :return: List(dict)
        """
        
        return [
            {
                'name': 'conda_env',
                'msg': 'Name of the conda environment for running Pyflextrkr',
                'type': str,
                'default': "flextrkr",
            },
            {
                'name': 'config',
                'msg': 'The config file for running analysis',
                'type': str,
                'default': None,
            },
            {
                'name': 'runscript',
                'msg': 'The name of the Pyflextrkr script to run (run_mcs_tbpfradar3d_wrf)',
                'type': str,
                'default': 'run_mcs_tbpfradar3d_wrf',
                'choices': ['run_mcs_tbpfradar3d_wrf', 'run_mcs_tbpf_saag_summer_sam', 'run_mcs_tb_summer_sam']
            },
            {
                'name': 'flush_mem',
                'msg': 'Flushing the memory after each stage',
                'type': bool,
                'default': False,
            },
            {
                'name': 'flush_mem_cmd',
                'msg': 'Command to flush the node memory',
                'type': str,
                'default': "ml user-scripts; sudo drop_caches", # for Ares
            },
            {
                'name': 'pyflextrkr_path',
                'msg': 'Absolute path to the Pyflextrkr source code',
                'type': str,
                'default': f"{Package(self.pkg_type).pkg_root}/src/PyFLEXTRKR",
            },
            {
                'name': 'experiment_input_path',
                'msg': 'Absolute path to the experiment run input and output files',
                'type': str,
                'default': None,
            },
            {
                'name': 'run_parallel',
                'msg': 'Parallel mode for Pyflextrkr: 0 (serial), 1 (local cluster), 2 (Dask MPI)',
                'type': int,
                'default': 1,
                'choices': [0,1,2],
            },
            {
                'name': 'nprocesses',
                'msg': 'Number of processes to run in parallel',
                'type': int,
                'default': 8,
            },
            {
                'name': 'run_cmd', # This is a internal variable
                'msg': 'Command to run Pyflextrkr',
                'type': str,
                'default': None,
            },
            {
                'name': 'local_exp_dir',
                'msg': 'Local experiment directory',
                'type': str,
                'default': None,
            },
            {
                'name': 'with_hermes',
                'msg': 'Whether it is used with Hermes (e.g. needs to update environment variables)',
                'type': bool,
                'default': False,
            },
        ]

    def _configure(self, **kwargs):
        """
        Converts the Jarvis configuration to application-specific configuration.

        :param kwargs: Configuration parameters for this pkg.
        :return: None
        """
        
        experiment_input_path = os.getenv('EXPERIMENT_INPUT_PATH')
        if experiment_input_path is None:
            raise Exception("Must set the experiment_input_path")
        else:
            self.config['experiment_input_path'] = experiment_input_path
        
        # update config file everytime
        self.config['config'] = f"{self.pkg_dir}/example_config/{self.config['runscript']}_template.yml"
        
        # Check if pyflextrkr_path not exists
        if pathlib.Path(self.config['pyflextrkr_path']).exists() == False:
            raise Exception(f"`pyflextrkr_path` {self.config['pyflextrkr_path']} does not exist.")
        
        if self.config['conda_env'] is None:
            raise Exception("Must set the conda environment for running Pyflextrkr")
        
        if self.config['runscript'] is None:
            raise Exception("Must set the Pyflextrkr script to run")
        else:
            
            # check if run script matches config file
            if self.config['runscript'] not in self.config['config']:
                raise Exception(f"Run script {self.config['runscript']} does not match config file {self.config['config']}")
            
            # get base file name without extension
            pass_in_path = self.config['runscript']
            script_name = pass_in_path.split("/")[-1]
            # remove ".py" from file name
            if ".py" in script_name:
                script_name = script_name[:-3]
            self.config['runscript'] = script_name

        # Check if config file exists
        if pathlib.Path(self.config['config']).exists():
            pass
        else:
            raise Exception(f"File {self.config['config']} does not exist.")

        if self.config['flush_mem'] == False:
            self.env['FLUSH_MEM'] = "FALSE"
        else:
            self.env['FLUSH_MEM'] = "TRUE"
            if self.config['flush_mem_cmd'] is None:
                raise Exception("Must add the command to flush memory using flush_mem_cmd")
        
        if self.config['pyflextrkr_path'] is None:
            raise Exception("Must set the `pyflextrkr_path` to the Pyflextrkr source code")
        else:
            # check that path exists
            pathlib.Path(self.config['pyflextrkr_path']).exists()
            # self.config['stdout'] = f'{self.config["pyflextrkr_path"]}/pyflextrkr_run.log'
        

    def _configure_yaml(self):
        self.env['HDF5_USE_FILE_LOCKING'] = "FALSE" # set HDF5 locking: FALSE, TRUE, BESTEFFORT

        yaml_file = self.config['config']
        
        if "_template.yml" not in str(yaml_file):
            yaml_file = yaml_file.replace(".yml", "_template.yml")
        
        self.log(f"Pyflextrkr config from: {yaml_file}")
        
        with open(yaml_file, "r") as stream:
            
            experiment_input_path = self.config['experiment_input_path']
            if self.config['local_exp_dir'] is not None:
                experiment_input_path = self.config['local_exp_dir']
            
            input_path = f"{experiment_input_path}/{self.config['runscript']}/"
            output_path = f"{experiment_input_path}/output_data/{self.config['runscript']}/"
            
            # Check if input_path exists and has files
            if pathlib.Path(input_path).exists() == False:
                raise Exception(f"Input path {input_path} does not exist.")
            if len(os.listdir(input_path)) == 0:
                raise Exception(f"Input path {input_path} is empty.")
            
            # pathlib.Path(input_path).mkdir(parents=True, exist_ok=True) # this should be done in data stage_in or setup
            pathlib.Path(output_path).mkdir(parents=True, exist_ok=True)
            
            try:
                config_vars = yaml.safe_load(stream)
                
                config_vars['dask_tmp_dir'] = f"/tmp/pyflextrkr_test"
                pathlib.Path(config_vars['dask_tmp_dir']).mkdir(parents=True, exist_ok=True)
                
                config_vars['clouddata_path'] = str(input_path)
                config_vars['root_path'] = str(output_path)
                
                # Set run mode
                config_vars['run_parallel'] = self.config['run_parallel']
                
                # check processes
                if self.config['run_parallel'] == 0 and self.config['nprocesses'] > 1:
                    self.log(f"WARNING: run_parallel is 0 (serial) nprocesses is set to 1")
                    self.config['nprocesses'] = 1
                config_vars['nprocesses'] = self.config['nprocesses']
                
                if self.config['nprocesses'] < config_vars['nprocesses']:
                    self.log(f"WARNING: nprocesses is less than config file, set to {config_vars['nprocesses']}")
                    self.config['nprocesses'] = config_vars['nprocesses']
                
                # check if landmask_filename is a key in config_vars
                if 'landmask_filename' in config_vars:
                    org_path = config_vars['landmask_filename']
                    landmask_path = org_path.replace('INPUT_DIR/', input_path)
                    landmask_path = landmask_path.replace("'", "") # remove single quotes format
                    
                    if pathlib.Path(landmask_path).exists():
                        config_vars['landmask_filename'] = str(landmask_path)
                    else:
                        raise Exception(f"File {landmask_path} does not exist.")
                
                # save config_vars back to yaml file
                new_yaml_file = yaml_file.replace("_template.yml", ".yml")
                yaml.dump(config_vars, open(new_yaml_file, 'w'), default_flow_style=False)
            except yaml.YAMLError as exc:
                self.log(exc)
        self.config['config'] = new_yaml_file 
            
    def _unset_vfd_vars(self,env_vars_toset):
        cmd = ['conda', 'env', 'config', 'vars', 'unset',]
        
        for env_var in env_vars_toset:
            cmd.append(f'{env_var}')
        cmd.append('-n')
        cmd.append(self.config['conda_env'])
        
        cmd = ' '.join(cmd)
        Exec(cmd, LocalExecInfo(env=self.mod_env,)).run()
        self.log(f"Pyflextrkr _unset_vfd_vars: {cmd}")

    def _set_env_vars(self, env_vars_toset):
        
        self.log(f"Pyflextrkr _set_env_vars")
        
        # Unset all env_vars_toset first
        self._unset_vfd_vars(env_vars_toset)

        cmd = [ 'conda', 'env', 'config', 'vars', 'set']
        for env_var in env_vars_toset:
            env_var_val = self.mod_env[env_var]
            cmd.append(f'{env_var}={env_var_val}')
        
        cmd.append('-n')
        cmd.append(self.config['conda_env'])
        cmd = ' '.join(cmd)
        self.log(f"Pyflextrkr _set_env_vars: {cmd}")
        Exec(cmd, LocalExecInfo(env=self.mod_env,)).run()
        
    
    def _construct_cmd(self):
        """
        Construct the command to launch the application. E.g., Pyflextrkr will
        launch with expected environment and number of srun processes.

        :return: None
        """
        self.clean()
        
        cmd = []
        if self.config['run_parallel'] == 1:
            cmd = [
            'conda','run', '-v','-n', self.config['conda_env'],
            ]
        elif self.config['run_parallel'] == 2:
            host_list_str = None
            
            # Check if self.hostfile is set
            if self.hostfile is None:
                raise Exception("Running with Dask-MPI mode but self.hostfile is None")
            
            # open self.hostfile to get all lines of hosts into a string deliminated by ,
            # self.log(f"Pyflextrkr hostfile: {self.hostfile}")
            if 'localhost' in self.hostfile:
                host_list_str = "127.0.0.1"
            else:
                for hostname in self.hostfile:
                    if host_list_str is None:
                        host_list_str = hostname.rstrip()
                    else:
                        host_list_str = host_list_str + "," + hostname.rstrip()
            
            if host_list_str is None:
                raise Exception("host_list_str is None")
            self.log(f"Pyflextrkr host_list_str: {host_list_str}")
            
            # mpirun --host $hostlist --npernode 2
            ppn = self.config['nprocesses']/len(self.hostfile)
            cmd = [
                'conda','run', '-v','-n', self.config['conda_env'],
                'mpirun',
                '--host', host_list_str,
                '-n', str(self.config['nprocesses']),
                '-ppn', str(int(ppn)),
                # '-env', f'HDF5_USE_FILE_LOCKING={self.config["HDF5_USE_FILE_LOCKING"]}',
            ]
        
        # Exec("which python")
        cmd.append('python')
        # Convert runscript to full .py file path
        if self.config['pyflextrkr_path'] and self.config['runscript']:
            cmd.append(f'{self.config["pyflextrkr_path"]}/runscripts/{self.config["runscript"]}.py')
        
        
        cmd.append(self.config['config'])

        self.config['run_cmd'] = ' '.join(cmd)

    def start(self):
        """
        Launch an application. E.g., Pyflextrkr will launch the servers, clients,
        and metadata services on all necessary pkgs.

        :return: None
        """
        
        if self.config['with_hermes'] == True:
            self._set_env_vars(self.hermes_env_vars)
        else:
            self._unset_vfd_vars(self.hermes_env_vars)
        
        ## Configure yaml file before start
        self._configure_yaml()
        self._construct_cmd()
        
        self.log(f"Pyflextrkr run_cmd: {self.config['run_cmd']}")
        
        start = time.time()
        
        Exec(self.config['run_cmd'],
             LocalExecInfo(env=self.mod_env,
                           pipe_stdout=self.config['stdout'],
                           pipe_stderr=self.config['stderr'],
                           )).run()
        
        end = time.time()
        diff = end - start
        self.log(f'Pyflextrkr TIME: {diff} seconds') # color=Color.GREEN
        

    def stop(self):
        """
        Stop a running application. E.g., Pyflextrkr will terminate the servers,
        clients, and metadata services.

        :return: None
        """
        pass
        
    def kill(self):
        """
        Stop a running application. E.g., Pyflextrkr will terminate the servers,
        clients, and metadata services.

        :return: None
        """
        cmd = ['killall', '-9', 'python']
        Exec(' '.join(cmd), LocalExecInfo(hostfile=self.hostfile)).run()

    def clean(self):
        """
        Destroy all data for an application. E.g., Pyflextrkr will delete all
        metadata and data directories in addition to the orangefs.xml file.

        :return: None
        """
        # self.log(f"Manual Exec Required: Please clean up files in {self.config['experiment_input_path']}")
        
        output_dir = self.config['experiment_input_path'] + f"/output_data/{self.config['runscript']}"
        if self.config['local_exp_dir'] is not None:
            output_dir = self.config['local_exp_dir'] + f"/output_data/{self.config['runscript']}"
        
        # recursive remove all files in output_data directory
        self.log(f'Removing {output_dir}')
        Rm(output_dir).run()
        
        ## Do not clear cache in script, clear cache manually
        # # Clear cache
        # self.log(f'Clearing cache')
        # Exec(self.config['flush_mem_cmd'], LocalExecInfo(env=self.mod_env,))
        
        # output_dir = self.config['output'] + "*"
        # self.log(f'Removing {output_dir}')
        # Rm(output_dir)
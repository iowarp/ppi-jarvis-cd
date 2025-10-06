"""
This module provides classes and methods to launch the Arldm application.
Arldm is ....
"""
from jarvis_cd.core.pkg import Application
from jarvis_cd.shell import Exec, LocalExecInfo
from jarvis_cd.shell.process import Rm
import os, pathlib
import time
import yaml
from scspkg.pkg import Package
import sys # for stdout, stderr

class Arldm(Application):
    """
    This class provides methods to launch the Arldm application.
    """
    def _init(self):
        """
        Initialize paths
        """
        self.pkg_type = 'arldm'
        self.hermes_env_vars = ['HERMES_ADAPTER_MODE', 'HERMES_CLIENT_CONF', 
                                'HERMES_CONF', 'LD_PRELOAD']
        # self.hermes_env_vars = ['HDF5_DRIVER', 'HDF5_PLUGIN_PATH', 
        #                   'HERMES_ADAPTER_MODE', 'HERMES_CLIENT_CONF',
        #                   'HERMES_CONF', 'HERMES_VFD', 'HERMES_POSIX'
        #                   ]
        
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
                'msg': 'Name of the conda environment for running ARLDM',
                'type': str,
                'default': "arldm",
            },
            {
                'name': 'config',
                'msg': 'The config file for running analysis',
                'type': str,
                'default': f'{self.pkg_dir}/example_config/config_template.yml',
            },
            {
                'name': 'update_envar_yml',
                'msg': 'Update the conda environment variables',
                'type': str,
                'default': f'{self.pkg_dir}/example_config/update_envar.yml',
            },
            {
                'name': 'with_hermes',
                'msg': 'Whether it is used with Hermes (e.g. needs to update environment variables)',
                'type': bool,
                'default': False,
            },
            {
                'name': 'with_dayu',
                'msg': 'Whether it is used with DaYu (e.g. needs to update task files)',
                'type': bool,
                'default': False,
            },
            {
                'name': 'runscript',
                'msg': 'The name of the ARLDM script to run',
                'type': str,
                'default': 'vistsis', # smallest dataset
                'choices': ['flintstones', 'pororo', 'vistsis', 'vistdii'],
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
                'name': 'arldm_path',
                'msg': 'Absolute path to the ARLDM source code (can set to `scspkg pkg src arldm`/ARLDM)',
                'type': str,
                'default': f"{Package(self.pkg_type).pkg_root}/src/ARLDM",
            },
            {
                'name': 'mode',
                'msg': 'Mode of running ARLDM: train(D) or sample',
                'type': str,
                'default': 'train',
                'choice': ['train', 'sample'],
            },
            {
                'name': 'num_workers',
                'msg': 'Number of CPU workers to use for parallel processing',
                'type': int,
                'default': 1,
                'choices': [0, 1, 2],
            },
            {
                'name': 'experiment_input_path',
                'msg': 'Absolute path to the experiment where you put all data',
                'type': str,
                'default': None,
            },
            {
                'name': 'sample_output_dir',
                'msg': 'Directory to save samples',
                'type': str,
                'default': None, 
            },
            {
                'name': 'hdf5_file',
                'msg': 'HDF5 file to save samples',
                'type': str,
                'default': None,
            },
            {
                'name': 'prep_hdf5',
                'msg': 'Prepare the HDF5 file for the ARLDM run',
                'type': bool,
                'default': True,
            },
            {
                'name': 'local_exp_dir',
                'msg': 'Local experiment directory',
                'type': str,
                'default': None,
            },
            {
                'name': 'pretrain_model_path',
                'msg': 'Pretrained model path',
                'type': str,
                'default': None,
            },
        ]

    def _configure_yaml(self):
        yaml_file = self.config['config']

        if "_template.yml" not in str(yaml_file):
            yaml_file = yaml_file.replace(".yml", "_template.yml")
        
        self.log(f"ARLDM template.yml: {yaml_file}")

        with open(yaml_file, "r") as stream:
            try:
                config_vars = yaml.safe_load(stream)
                
                run_test = self.config['runscript']
                
                config_vars['mode'] = self.config['mode']
                config_vars['num_workers'] = self.config['num_workers']
                config_vars['run_name'] = f"{self.config['runscript']}_{self.config['mode']}"
                config_vars['dataset'] = run_test

                experiment_input_path = self.config['experiment_input_path']
                if self.config['local_exp_dir'] is not None:
                    experiment_input_path = self.config['local_exp_dir']
                    self.config['ckpt_dir'] = experiment_input_path + f"/{self.config['runscript']}_save_ckpt"
                    self.config['sample_output_dir'] = experiment_input_path + f"/sample_out_{self.config['runscript']}_{self.config['mode']}"
                    self.config['hdf5_file'] = f"{experiment_input_path}/{self.config['runscript']}_out.h5"

                config_vars['ckpt_dir'] = self.config['ckpt_dir']
                config_vars['sample_output_dir'] = self.config['sample_output_dir']
                config_vars[run_test]['hdf5_file'] = self.config['hdf5_file']
                
                # save config_vars back to yaml file
                new_yaml_file = yaml_file.replace("_template.yml", ".yml")
                yaml.dump(config_vars, open(new_yaml_file, 'w'), default_flow_style=False)
            except yaml.YAMLError as exc:
                self.log(exc)
        self.config['config'] = new_yaml_file
        

    def _configure(self, **kwargs):
        """
        Converts the Jarvis configuration to application-specific configuration.
        E.g., OrangeFS produces an orangefs.xml file.

        :param kwargs: Configuration parameters for this pkg.
        :return: None
        """
        # self.env['HDF5_USE_FILE_LOCKING'] = "FALSE" 
        # self.env['HYDRA_FULL_ERROR'] = "1" # complete stack trace.
        
        self.log(f"ARLDM _configure")
        
        self.setenv('HDF5_USE_FILE_LOCKING', "FALSE") # set HDF5 locking: FALSE, TRUE, BESTEFFORT
        self.setenv('HYDRA_FULL_ERROR', "1")
        
        if self.config['pretrain_model_path'] is None:
            pretrain_model_path = os.getenv('PRETRAIN_MODEL_PATH')
            if pretrain_model_path is not None:
                if self.config['local_exp_dir'] is not None:
                    pretrain_model_path = self.config['local_exp_dir'] + "/model_large.pth"
                self.log(f"PRETRAIN_MODEL_PATH: {pretrain_model_path}")
                self.config['pretrain_model_path'] = pretrain_model_path
                # self.env['PRETRAIN_MODEL_PATH'] = pretrain_model_path
                self.setenv('PRETRAIN_MODEL_PATH', pretrain_model_path)
            else:
                raise Exception("Must set the pretrain_model_path")
        else:
            if self.config['local_exp_dir'] is None:
                pretrain_model_path = os.getenv('PRETRAIN_MODEL_PATH')
                if pretrain_model_path is not None:
                    self.log(f"PRETRAIN_MODEL_PATH: {pretrain_model_path}")
                    self.config['pretrain_model_path'] = pretrain_model_path
                    # self.env['PRETRAIN_MODEL_PATH'] = pretrain_model_path
                    self.setenv('PRETRAIN_MODEL_PATH', pretrain_model_path)
        
        experiment_input_path = os.getenv('EXPERIMENT_INPUT_PATH')
        if experiment_input_path is None:
            raise Exception("Must set the experiment_input_path")
        else:
            self.config['experiment_input_path'] = experiment_input_path
        
        if self.config['conda_env'] is None:
            raise Exception("Must set the conda environment for running ARLDM")
        if self.config['config'] is None:
            raise Exception("Must set the ARLDM config file")
        if self.config['runscript'] is None:
            raise Exception("Must set the ARLDM script to run")
            
        if self.config['flush_mem'] == False:
            self.env['FLUSH_MEM'] = "FALSE"
        else:
            if self.config['flush_mem_cmd'] is None:
                raise Exception("Must add the command to flush memory using flush_mem_cmd")
        
        if self.config['arldm_path'] is None:
            raise Exception("Must set the `'arldm_path'` to the ARLDM source code")
        else:
            # check that path exists
            if not pathlib.Path(self.config['arldm_path']).exists():
                raise Exception(f"`'arldm_path'` does not exist: {self.config['arldm_path']}")
        
        # check and make -p experiment_input_path
        pathlib.Path(self.config['experiment_input_path']).mkdir(parents=True, exist_ok=True)
        
        # set ckpt_dir
        self.config['ckpt_dir'] = f'{self.config["experiment_input_path"]}/{self.config["runscript"]}_save_ckpt'
        pathlib.Path(self.config['ckpt_dir']).mkdir(parents=True, exist_ok=True)
        
        # set sample_output_dir
        self.config['sample_output_dir'] = f'{self.config["experiment_input_path"]}/sample_out_{self.config["runscript"]}_{self.config["mode"]}'
        pathlib.Path(self.config['sample_output_dir']).mkdir(parents=True, exist_ok=True)
        
        # set sample_output_dir
        self.config['hdf5_file'] = f'{self.config["experiment_input_path"]}/{self.config["runscript"]}_out.h5'
                
        self._configure_yaml()
        

    def _prep_hdf5_file(self):
        """
        Prepare the HDF5 file for the ARLDM run
        """
        if self.config['with_dayu'] == True:
            self._set_curr_task_file("arldm_saveh5")
        
        self.log(f"ARLDM _prep_hdf5_file input from to {self.config['hdf5_file']}")
        
        experiment_input_path = self.config['experiment_input_path']
        if self.config['local_exp_dir'] is not None:
            experiment_input_path = self.config['local_exp_dir']
        
        cmd = [
            # f"cd {self.config['arldm_path']}; echo Executing from directory `pwd`;",
            'conda','run', '-n', self.config['conda_env'], # conda environment
            'python',
        ]

        if self.config['runscript'] == 'pororo':
            cmd.append(f'{self.config["arldm_path"]}/data_script/pororo_hdf5.py')
            cmd.append(f'--data_dir {experiment_input_path}/pororo')
            cmd.append(f'--save_path {self.config["hdf5_file"]}')
        elif self.config['runscript'] == 'flintstones':
            cmd.append(f'{self.config["arldm_path"]}/data_script/flintstones_hdf5.py')
            cmd.append(f'--data_dir {experiment_input_path}/flintstones')
            cmd.append(f'--save_path {self.config["hdf5_file"]}')
        elif self.config['runscript'] == 'vistsis' or self.config['runscript'] == 'vistdii':
            cmd.append(f'{self.config["arldm_path"]}/data_script/vist_hdf5.py')
            # experiment_input_path = f'{experiment_input_path}/{self.config["runscript"]}'
            cmd.append(f'--sis_json_dir {experiment_input_path}/vistsis')
            cmd.append(f'--dii_json_dir {experiment_input_path}/vistdii')
            cmd.append(f'--img_dir {experiment_input_path}/visit_img')
            cmd.append(f'--save_path {self.config["hdf5_file"]}')
        else:
            raise Exception("Must set the correct ARLDM script to run")
        
        prep_cmd = ' '.join(cmd)
        
        start = time.time()
        Exec(prep_cmd, LocalExecInfo(
            env=self.mod_env,
            cwd=self.config['arldm_path'])).run()
        
        end = time.time()
        diff = end - start
        self.log(f'TIME: {diff} seconds') # color=Color.GREEN
        
        # check if hdf5_file exists
        if pathlib.Path(self.config['hdf5_file']).exists():
           self.log(f"HDF5 file created: {self.config['hdf5_file']}")
        else:
            raise Exception(f"HDF5 file not created: {self.config['hdf5_file']}") 
    
    def _train(self):
        """
        Run the ARLDM training run
        """
        if self.config['with_dayu'] == True:
            self._set_curr_task_file("arldm_train")
        
        self.log(f"ARLDM _train: dataset[{self.config['runscript']}]")
        
        # Move config file to arldm_path
        Exec(f"cp {self.config['config']} {self.config['arldm_path']}/config.yaml",
             LocalExecInfo(env=self.mod_env,)).run()
        
        
        cmd = [
            'conda','run', '-n', self.config['conda_env'], # conda environment
            'python'
        ]

        if self.config['arldm_path'] and self.config['runscript']:
            cmd.append(f'{self.config["arldm_path"]}/main.py')
        
        conda_cmd = ' '.join(cmd)
        
        start = time.time()

        self.jutil.debug_local_exec = True
        Exec(conda_cmd,
             LocalExecInfo(env=self.mod_env,
                           pipe_stdout=self.config['stdout'],
                           pipe_stderr=self.config['stderr'],
                           cwd=self.config['arldm_path'])).run()
        self.jutil.debug_local_exec = False
        
        end = time.time()
        diff = end - start
        self.log(f'TIME: {diff} seconds') # color=Color.GREEN
    
    def _sample(self):
        """
        Run the ARLDM sampling run
        
        This step can only be run when training is fully completed. 
        Currently train is set to fast_dev_run.
        """
        self.log(f"ARLDM sampling run: not implemented yet")

    def _set_curr_task_file(self,task):
        
        workflow_name = self.mod_env['WORKFLOW_NAME']
        path_for_task_files = self.mod_env['PATH_FOR_TASK_FILES']
        vfd_task_file = None
        vol_task_file = None
        
        if workflow_name and path_for_task_files:
            vfd_task_file = os.path.join(path_for_task_files, f"{workflow_name}_vfd.curr_task")
            vol_task_file = os.path.join(path_for_task_files, f"{workflow_name}_vol.curr_task")
            # Create file and parent file if it does not exist
            pathlib.Path(vfd_task_file).mkdir(parents=True, exist_ok=True)
            pathlib.Path(vol_task_file).mkdir(parents=True, exist_ok=True)
            

        # vfd_task_file = /tmp/$USER/pyflextrkr_vfd.curr_task
        
        if vfd_task_file and os.path.exists(vfd_task_file):
            if os.path.isfile(vfd_task_file):
                with open(vfd_task_file, "w") as file:
                    file.write(task)
                print(f"Overwrote: {vfd_task_file} with {task}")

        if vol_task_file and os.path.exists(vol_task_file):
            if os.path.isfile(vol_task_file):
                with open(vol_task_file, "w") as file:
                    file.write(task)
                print(f"Overwrote: {vol_task_file} with {task}")
        else:
            print("Invalid or missing PATH_FOR_TASK_FILES environment variable.")    

    def _unset_vfd_vars(self,env_vars_toset):
        cmd = ['conda', 'env', 'config', 'vars', 'unset',]
        
        for env_var in env_vars_toset:
            cmd.append(f'{env_var}')
        cmd.append('-n')
        cmd.append(self.config['conda_env'])
        
        cmd = ' '.join(cmd)
        Exec(cmd, LocalExecInfo(env=self.mod_env,)).run()
        self.log(f"ARLDM _unset_vfd_vars: {cmd}")

    def _set_env_vars(self, env_vars_toset):
        
        self.log(f"ARLDM _set_env_vars")
        
        # Unset all env_vars_toset first        
        self._unset_vfd_vars(env_vars_toset)

        cmd = [ 'conda', 'env', 'config', 'vars', 'set']
        for env_var in env_vars_toset:
            env_var_val = self.mod_env[env_var]
            cmd.append(f'{env_var}={env_var_val}')
        
        cmd.append('-n')
        cmd.append(self.config['conda_env'])
        cmd = ' '.join(cmd)
        self.log(f"ARLDM _set_env_vars: {cmd}")
        Exec(cmd, LocalExecInfo(env=self.mod_env,)).run()

    def start(self):
        """
        Launch an application. E.g., OrangeFS will launch the servers, clients,
        and metadata services on all necessary pkgs.

        :return: None
        """
        
        self._configure_yaml()
        
        if self.config['with_hermes'] == True:
            self._set_env_vars(self.hermes_env_vars)
        else:
            self._unset_vfd_vars(self.hermes_env_vars)
        
        
        self.log(f"ARLDM start")
        
        start = time.time()
        
        if self.config['prep_hdf5']:
            self._prep_hdf5_file()
        
        if self.config['mode'] == 'train':
            self._train()
        
        if self.config['mode'] == 'sample':
            self._sample()
        
        end = time.time()
        diff = end - start
        self.log(f'TOTAL RUN TIME: {diff} seconds')


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
        output_h5 = self.config['experiment_input_path'] + f"/{self.config['runscript']}_out.h5"
        output_dir = self.config['experiment_input_path'] + f"/sample_out_{self.config['runscript']}_{self.config['mode']}"
        if self.config['local_exp_dir'] is not None:
            output_dir = self.config['local_exp_dir'] + f"/sample_out_{self.config['runscript']}_{self.config['mode']}"
        
        # recursive remove all files in output_data directory
        if os.path.exists(output_dir):
            self.log(f'Removing {output_dir}')
            Rm(output_dir).run()
        else:
            self.log(f'No directory to remove: {output_dir}')
        
        if os.path.exists(output_h5):     
            self.log(f'Removing {output_h5}')
            Rm(output_h5).run()
        else:
            self.log(f'No file to remove: {output_h5}')
        
        ## Clear cache manually
        # # Clear cache
        # self.log(f'Clearing cache')
        # Exec(self.config['flush_mem_cmd'], LocalExecInfo(env=self.mod_env,))

"""
This module provides classes and methods to launch the Ddmd application.
Ddmd is ....
"""
from jarvis_cd.core.pkg import Application
from jarvis_cd.shell import Exec, LocalExecInfo, PsshExecInfo
from jarvis_cd.shell.process import Kill, Rm
import os
import yaml
import time
import pathlib, glob, shutil

class Ddmd(Application):
    """
    This class provides methods to launch the Ddmd application.
    """
    def _init(self):
        """
        Initialize paths
        """
        self.openmm_list = []
        self.aggregate = None
        self.train = None
        self.prev_model_json = None
        self.inference = None
        self.hermes_env_vars = ['HERMES_ADAPTER_MODE', 'HERMES_CLIENT_CONF', 'HERMES_CONF', 'LD_PRELOAD']

    def _configure_menu(self):
        """
        Create a CLI menu for the configurator method.
        For thorough documentation of these parameters, view:
        https://github.com/scs-lab/jarvis-util/wiki/3.-Argument-Parsing

        :return: List(dict)
        """
        return [
            {
                'name': 'conda_openmm',
                'msg': 'Name of the conda environment for running OpenMM',
                'type': str,
                'default': None,
            },
            {
                'name': 'conda_pytorch',
                'msg': 'Name of the conda environment for running PyTorch',
                'type': str,
                'default': None,
            },
            {
                'name': 'ddmd_path',
                'msg': 'Path to the DDMD source code',
                'type': str,
                'default': None, # `scspkg pkg src ddmd`deepdrivemd/
            },
            {
                'name': 'experiment_path',
                'msg': 'Absolute path to the experiment run input and output files',
                'type': str,
                'default': '${HOME}/experiments/ddmd_test',
            },
            {
                'name': 'local_exp_dir',
                'msg': 'Local experiment directory',
                'type': str,
                'default': None,
            },
            {
                'name': 'molecules_path',
                'msg': 'Absolute path to the molecules submodule directory',
                'type': str,
                'default': None,
            },
            {
                'name': 'md_runs',
                'msg': 'Number of MD runs to perform',
                'type': int,
                'default': 12,
            },
            {
                'name': 'iter_count',
                'msg': 'Number of iterations to perform',
                'type': int,
                'default': 1,
            },
            {
                'name': 'sim_len',
                'msg': 'Length of simulation size (e.g., 0.1. 1)',
                'type': float,
                'default': 0.1,
            },
            {
                'name': 'nnodes',
                'msg': 'Number of nodes to use',
                'type': int,
                'default': 1,
            },
            {
                'name': 'gpu_per_node',
                'msg': 'Number of GPUs per node',
                'type': int,
                'default': 1,
            },
            {
                'name': 'md_start',
                'msg': 'Starting MD run',
                'type': int,
                'default': 0,
            },
            {
                'name': 'md_slide',
                'msg': 'Number of MD runs to slide',
                'type': int,
                'default': 0, # $MD_RUNS/$NODE_COUNT
            },
            {
                'name': 'stage_idx',
                'msg': 'Stage index (starting at 0)',
                'type': int,
                'default': 0, # Usually don't change this
            },
            {
                'name': 'skip_sim',
                'msg': 'Skip the simulation stage',
                'type': bool,
                'default': False,
            },
            {
                'name': 'short_pipe',
                'msg': 'Use a shorted pipeline',
                'type': bool,
                'default': False,
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
        E.g., OrangeFS produces an orangefs.xml file.

        :param kwargs: Configuration parameters for this pkg.
        :return: None
        """
        
        if self.config['conda_openmm'] is None:
            # check if CONDA_OPENMM is set in the environment
            if os.environ.get('CONDA_OPENMM') is not None:
                self.config['conda_openmm'] = os.environ.get('CONDA_OPENMM') 
                self.env['CONDA_OPENMM'] = os.environ.get('CONDA_OPENMM')
            else:
                raise Exception('No conda_openmm environment specified')
            
        if self.config['conda_pytorch'] is None:
            if os.environ.get('CONDA_PYTORCH') is not None:
                self.config['conda_pytorch'] = os.environ.get('CONDA_PYTORCH')
                self.env['CONDA_PYTORCH'] = self.config['conda_pytorch']
            else:
                raise Exception('No conda_pytorch environment specified')
        
        if self.config['ddmd_path'] is None:
            if os.environ.get('DDMD_PATH') is not None:
                self.config['ddmd_path'] = os.environ.get('DDMD_PATH')
                self.env['DDMD_PATH'] = self.config['ddmd_path']
                self.config['molecules_path'] = self.config['ddmd_path'] + '/submodules/molecules'
                self.env['MOLECULES_PATH'] = self.config['molecules_path']
            else:
                raise Exception('No ddmd_path specified')
        else:
            self.env['DDMD_PATH'] = self.config['ddmd_path']
            self.config['molecules_path'] = self.config['ddmd_path'] + '/submodules/molecules'
            self.env['MOLECULES_PATH'] = self.config['molecules_path']
        
        if self.config['experiment_path'] is not None:
            self.config['experiment_path'] = os.path.expandvars(self.config['experiment_path'])
            self.env['EXPERIMENT_PATH'] = self.config['experiment_path']
            pathlib.Path(self.config['experiment_path']).mkdir(parents=True, exist_ok=True)
            
        if self.config['experiment_path'] is None:
            raise Exception('No experiment_path specified')
        
        if self.config['md_runs'] < 12:
            raise Exception('md_runs must be at least 12')
        
        if self.config['iter_count'] < 1:
            raise Exception('iter_count must be at least 1')
        
        if self.config['sim_len'] < 0.1:
            raise Exception('sim_len must be at least 0.1')
        
        if self.config['nnodes'] < 1:
            raise Exception('nnodes must be at least 1')
        
        self.config['md_slide'] = self.config['md_runs'] / self.config['nnodes']
    
    def _run_openmm(self):
        """
        Run the OpenMM simulation. This method is called by the run method.

        :return: None
        """
        
        all_tasks = []
        
        for task in range(self.config['md_start'], self.config['md_runs']):
        
            task_idx = "task" + str(task).zfill(4)
            stage_idx = "stage" + str(self.config['stage_idx']).zfill(4)
            gpu_idx = 0 # dummy now
            stage_name="molecular_dynamics"
            
            node_idx = len(self.hostfile) % self.config['nnodes']
            node_name = self.hostfile[node_idx]
            
            yaml_path = self.config['ddmd_path'] + "/test/bba/" + stage_name + "_stage_test.yaml"
            dest_path= self.config['experiment_path'] + "/" + stage_name + "_runs/" + stage_idx + "/" + task_idx
            
            # create the dest_path
            pathlib.Path(dest_path).mkdir(parents=True, exist_ok=True)
            
            # load yaml file to change the parameters
            with open(yaml_path, 'r') as f:
                config_vars = yaml.load(f, Loader=yaml.FullLoader)
                # sed -e "s/\$SIM_LENGTH/${SIM_LENGTH}/" -e "s/\$OUTPUT_PATH/${dest_path//\//\\/}/" -e "s/\$EXPERIMENT_PATH/${EXPERIMENT_PATH//\//\\/}/" -e "s/\$DDMD_PATH/${DDMD_PATH//\//\\/}/" -e "s/\$GPU_IDX/${gpu_idx}/" -e "s/\$STAGE_IDX/${STAGE_IDX}/" $yaml_path  > $dest_path/$(basename $yaml_path)
                config_vars['output_path'] = dest_path
                config_vars['experiment_directory'] = self.config['experiment_path']
                config_vars['initial_pdb_dir'] = self.config['ddmd_path'] + "/data/bba"
                config_vars['pdb_file'] = self.config['ddmd_path'] + "/data/bba/system/1FME-unfolded.pdb"
                config_vars['ddmd_path'] = self.config['ddmd_path']
                config_vars['reference_pdb_file'] = self.config['ddmd_path'] + "/data/bba/1FME-folded.pdb"
                
                config_vars['simulation_length_ns'] = self.config['sim_len']
                config_vars['gpu_idx'] = gpu_idx
                config_vars['stage_idx'] = self.config['stage_idx']
                config_vars['task_idx'] = task
                
                new_yaml_file = dest_path + "/" + stage_name + "_stage_test.yaml"
                yaml.dump(config_vars, open(new_yaml_file, 'w'), default_flow_style=False)
            
            logfile = dest_path + "/" + task_idx + "_OPENMM.log"
            
            cmd = [
                f'cd {dest_path};',
                'conda','run', '-n', self.config['conda_openmm'],
                'mpirun',
                '--host', node_name,
                '-np', str(1),
                '-env',
                f'PYTHONPATH={self.config["ddmd_path"]}:{self.config["molecules_path"]}',
                'python',
                f'{self.config["ddmd_path"]}/deepdrivemd/sim/openmm/run_openmm.py',
                '-c', new_yaml_file,
            ]
            
            conda_cmd = ' '.join(cmd)
            print(F"Running OpenMM on {node_name}: {dest_path}")
            print(f"{conda_cmd} > {logfile}")
            cur_task = Exec(conda_cmd, LocalExecInfo(env=self.mod_env,
                                          pipe_stdout=logfile,
                                          exec_async=True)).run()
            
            all_tasks.append(cur_task)
        
        return all_tasks
        
    
    
    def _run_aggregate(self):
        """
        Aggregate the results of the OpenMM simulation.
        
        :return: None
        """
        task_idx = "task0000" # fix to 0
        stage_name="aggregate"
        
        stage_idx = "stage" + str((self.config['stage_idx'])).zfill(4)
        node_idx = 0 # TODO: allow specify nodes?
        node_name = self.hostfile[node_idx]
        yaml_path = self.config['ddmd_path'] + "/test/bba/" + stage_name + "_stage_test.yaml"
        dest_path= self.config['experiment_path'] + "/" + stage_name + "_runs/" + stage_idx + "/" + task_idx
        # create the dest_path
        pathlib.Path(dest_path).mkdir(parents=True, exist_ok=True)
        
        # load yaml file to change the parameters
        with open(yaml_path, 'r') as f:
            config_vars = yaml.load(f, Loader=yaml.FullLoader)
            # sed -e "s/\$SIM_LENGTH/${SIM_LENGTH}/" -e "s/\$OUTPUT_PATH/${dest_path//\//\\/}/" -e "s/\$EXPERIMENT_PATH/${EXPERIMENT_PATH//\//\\/}/" -e "s/\$DDMD_PATH/${DDMD_PATH//\//\\/}/" -e "s/\$GPU_IDX/${gpu_idx}/" -e "s/\$STAGE_IDX/${STAGE_IDX}/" $yaml_path  > $dest_path/$(basename $yaml_path)
            config_vars['experiment_directory'] = self.config['experiment_path']
            config_vars['stage_idx'] = self.config['stage_idx']
            config_vars['task_idx'] = 0 # fix to 0
            config_vars['output_path'] = dest_path + "/aggregated.h5"
            config_vars['pdb_file'] = self.config['ddmd_path'] + "/data/bba/system/1FME-unfolded.pdb"
            config_vars['reference_pdb_file'] = self.config['ddmd_path'] + "/data/bba/1FME-folded.pdb"
            config_vars['simulation_length_ns'] = self.config['sim_len']
            
            
            new_yaml_file = dest_path + "/" + stage_name + "_stage_test.yaml"
            yaml.dump(config_vars, open(new_yaml_file, 'w'), default_flow_style=False)
            
            logfile = dest_path + "/" + task_idx + "_AGGREGATE.log"
            
            cmd = [
                f'cd {dest_path};',
                'conda','run', '-n', self.config['conda_openmm'],
                'mpirun',
                '--host', node_name,
                '-np', str(1),
                '-env',
                f'PYTHONPATH={self.config["ddmd_path"]}',
                'python',
                f'{self.config["ddmd_path"]}/deepdrivemd/aggregation/basic/aggregate.py',
                '-c', new_yaml_file,
            ]
            
            conda_cmd = ' '.join(cmd)
            print(F"Running Aggregate on {node_name}: {dest_path}")
            print(f"{conda_cmd} > {logfile}")
            Exec(conda_cmd, LocalExecInfo(env=self.mod_env,
                                        pipe_stdout=logfile)).run()
    
    
    def _run_train(self):
        """
        Train the model.
        
        :return: None
        """
        task_idx = "task0000" # fix to 0
        
        stage_idx = "stage" + str((self.config['stage_idx'])).zfill(4)
        model_tag = stage_idx + "_" + task_idx
        node_idx = 0 # TODO: allow specify nodes?
        node_name = self.hostfile[node_idx]
        dest_path= self.config['experiment_path'] + "/" + "machine_learning" + "_runs/" + stage_idx + "/" + task_idx
        stage_name="machine_learning" # "machine_learning" : faster, "training" : slower
        yaml_path = self.config['ddmd_path'] + "/test/bba/" + stage_name + "_stage_test.yaml"
        # create the dest_path
        pathlib.Path(dest_path).mkdir(parents=True, exist_ok=True)
        
        model_select_path = self.config['experiment_path'] + "/model_selection_runs/" + stage_idx + "/" + task_idx
        pathlib.Path(model_select_path).mkdir(parents=True, exist_ok=True)
        
        cp_cmd = [
            'cp','-p',
            f'{self.config["ddmd_path"]}/test/bba/stage0000_task0000.json',
            f'{model_select_path}/{model_tag}.json',
        ]
        cp_cmd = ' '.join(cp_cmd)
        print(f"Copying {model_tag}.json to {model_select_path}")
        Exec(cp_cmd, LocalExecInfo(env=self.mod_env)).run()
        
        self.prev_model_json = f'{model_select_path}/{model_tag}.json'
        
        try:
            # load yaml file to change the parameters
            with open(yaml_path, 'r') as f:
                config_vars = yaml.load(f, Loader=yaml.FullLoader)
                # sed -e "s/\$SIM_LENGTH/${SIM_LENGTH}/" -e "s/\$OUTPUT_PATH/${dest_path//\//\\/}/" -e "s/\$EXPERIMENT_PATH/${EXPERIMENT_PATH//\//\\/}/" -e "s/\$DDMD_PATH/${DDMD_PATH//\//\\/}/" -e "s/\$GPU_IDX/${gpu_idx}/" -e "s/\$STAGE_IDX/${STAGE_IDX}/" $yaml_path  > $dest_path/$(basename $yaml_path)
                config_vars['experiment_directory'] = self.config['experiment_path']
                config_vars['stage_idx'] = self.config['stage_idx']
                config_vars['task_idx'] = 0 # fix to 0
                config_vars['output_path'] = dest_path
                config_vars['model_tag'] = model_tag
                config_vars['init_weights_path'] = "none"
                
                new_yaml_file = dest_path + "/" + stage_name + "_stage_test.yaml"
                yaml.dump(config_vars, open(new_yaml_file, 'w'), default_flow_style=False)
                
                logfile = dest_path + "/" + task_idx + "_TRAIN.log"
                
                cmd = [
                    f'cd {dest_path};',
                    'conda','run', '-n', self.config['conda_pytorch'],
                    'mpirun',
                    '--host', node_name,
                    '-np', str(1),
                    '-env',
                    f'PYTHONPATH={self.config["ddmd_path"]}:{self.config["molecules_path"]}',
                    'python',
                    f'{self.config["ddmd_path"]}/deepdrivemd/models/aae/train.py',
                    '-c', new_yaml_file,
                ]
                
                conda_cmd = ' '.join(cmd)
                print(F"Running Training on {node_name}: {dest_path}")
                print(f"{conda_cmd} > {logfile}")
                curr_task = Exec(conda_cmd, LocalExecInfo(env=self.mod_env,
                                            pipe_stdout=logfile,
                                            exec_async=True)).run()
                return curr_task
        except Exception as e:
            print("ERROR: " + str(e))
            print("ERROR: Training failed")
            return None
    
    def _run_inference(self):
        """
        Run inference on the model.
        
        :return: None
        """
        task_idx = "task0000" # fix to 0
        
        stage_idx = "stage" + str((self.config['stage_idx'])).zfill(4)
        model_tag = stage_idx + "_" + task_idx
        node_idx = 0 
        if len(self.hostfile) > 1:
            node_idx = 1 # TODO: allow specify nodes?
        node_name = self.hostfile[node_idx]
        stage_name="inference" 
        dest_path= self.config['experiment_path'] + f"/{stage_name}_runs/" + stage_idx + "/" + task_idx
        yaml_path = self.config['ddmd_path'] + "/test/bba/" + stage_name + "_stage_test.yaml"
        # create the dest_path
        pathlib.Path(dest_path).mkdir(parents=True, exist_ok=True)
        
        agent_run_path = self.config['experiment_path'] + "/agent_runs/" + stage_idx + "/" + task_idx
        pathlib.Path(agent_run_path).mkdir(parents=True, exist_ok=True)
        
        pretrained_model = self.config['ddmd_path'] + "/data/bba/epoch-130-20201203-150026.pt"
        
        checkpoint_path_pattern = os.path.join(self.config['experiment_path'], "machine_learning_runs", "*", "*", "checkpoint")
        # Find all matching checkpoint directories
        matching_checkpoint_dirs = glob.glob(checkpoint_path_pattern)
        if matching_checkpoint_dirs:
            # Construct the complete file path pattern for checkpoint files
            checkpoint_pattern = os.path.join(matching_checkpoint_dirs[0], '*.pt')
            # Find all matching checkpoint files
            checkpoint_files = glob.glob(checkpoint_pattern)
            # Check if there are any .pt files in the matching checkpoint directory
            if checkpoint_files:

                # Sort files by epoch and timestamp and get the latest checkpoint
                # latest_checkpoint = max(checkpoint_files, key=os.path.getmtime) # getctime, this does not get epoch 10
                latest_checkpoint = max(checkpoint_files, key=lambda x: (int(x.split('-')[1]), int(x.split('-')[2]), int(x.split('-')[3].split('.')[0])))
                print(f"Latest checkpoint: {latest_checkpoint}")
                
            else:
                latest_checkpoint = pretrained_model
        else:
            print(f"Using pretrained model: {pretrained_model}")
            latest_checkpoint = pretrained_model
        
        prev_stage_idx = "stage" + str((self.config['stage_idx']-1)).zfill(4)
        # replace $MODEL_CHECKPOINT with latest_checkpoint in the json file
        with open(self.prev_model_json, 'r') as f:
            json_str = f.read()
            json_str = json_str.replace("$MODEL_CHECKPOINT", latest_checkpoint)

        # save the updated json content back to the file
        with open(self.prev_model_json, 'w') as f:
            f.write(json_str)

        try:
            # load yaml file to change the parameters
            with open(yaml_path, 'r') as f:
                config_vars = yaml.load(f, Loader=yaml.FullLoader)
                # sed -e "s/\$SIM_LENGTH/${SIM_LENGTH}/" -e "s/\$OUTPUT_PATH/${dest_path//\//\\/}/" -e "s/\$EXPERIMENT_PATH/${EXPERIMENT_PATH//\//\\/}/" -e "s/\$DDMD_PATH/${DDMD_PATH//\//\\/}/" -e "s/\$GPU_IDX/${gpu_idx}/" -e "s/\$STAGE_IDX/${STAGE_IDX}/" $yaml_path  > $dest_path/$(basename $yaml_path)
                config_vars['experiment_directory'] = self.config['experiment_path']
                config_vars['stage_idx'] = self.config['stage_idx']
                config_vars['task_idx'] = 0 # fix to 0
                config_vars['output_path'] = dest_path
                
                new_yaml_file = dest_path + "/" + stage_name + "_stage_test.yaml"
                yaml.dump(config_vars, open(new_yaml_file, 'w'), default_flow_style=False)
                
                logfile = dest_path + "/" + task_idx + "_INFERENCE.log"
                
                cmd = [
                    f'cd {dest_path};',
                    'conda','run', '-n', self.config['conda_pytorch'],
                    'mpirun',
                    '--host', node_name,
                    '-np', str(1),
                    '-env',
                    'OMP_NUM_THREADS=4',
                    '-env',
                    f'PYTHONPATH={self.config["ddmd_path"]}:{self.config["molecules_path"]}',
                    'python',
                    f'{self.config["ddmd_path"]}/deepdrivemd/agents/lof/lof.py',
                    '-c', new_yaml_file,
                ]
                
                conda_cmd = ' '.join(cmd)
                print(F"Running Inference on {node_name}: {dest_path}")
                print(f"{conda_cmd} > {logfile}")
                curr_task = Exec(conda_cmd, LocalExecInfo(env=self.mod_env,
                                            pipe_stdout=logfile)).run()
                return curr_task
        except Exception as e:
            print("ERROR: " + str(e))
            print("ERROR: Inference failed")
            return None
    
    def _check_openmm(self):
        """
        Check if all the OpenMM files exist
        """
        for task in range(self.config['md_start'], self.config['md_runs']):
        
            task_idx = "task" + str(task).zfill(4)
            stage_idx = "stage" + str(self.config['stage_idx']).zfill(4)
            stage_name="molecular_dynamics"
            dest_path= self.config['experiment_path'] + "/" + stage_name + "_runs/" + stage_idx + "/" + task_idx
            
            # Check if "*.h5" and "*.pdb" files exist and not size 0
            h5_path_pattern = os.path.join(dest_path, '*.h5')
            matching_h5_files = glob.glob(h5_path_pattern)
            pdb_path_pattern = os.path.join(dest_path, '*.pdb')
            matching_pdb_files = glob.glob(pdb_path_pattern)
            if matching_h5_files and matching_pdb_files:
                continue
            else:
                return False
        return True

    def _unset_vfd_vars(self,env_vars_toset):
        
        conda_envs = [self.config['conda_openmm'], self.config['conda_pytorch']]
        
        for cenv in conda_envs:
        
            cmd = ['conda', 'env', 'config', 'vars', 'unset',]
            
            for env_var in env_vars_toset:
                cmd.append(f'{env_var}')
            cmd.append('-n')
            cmd.append(cenv)
            
            cmd = ' '.join(cmd)
            Exec(cmd, LocalExecInfo(env=self.mod_env,)).run()
            self.log(f"DDMD _unset_vfd_vars for {cenv}: {cmd}")

    def _set_env_vars(self, env_vars_toset):
        
        conda_envs = [self.config['conda_openmm'], self.config['conda_pytorch']]
        
        for cenv in conda_envs:
            
            # Unset all env_vars_toset first
            self._unset_vfd_vars(env_vars_toset)

            cmd = [ 'conda', 'env', 'config', 'vars', 'set']
            for env_var in env_vars_toset:
                env_var_val = self.mod_env[env_var]
                cmd.append(f'{env_var}={env_var_val}')
            
            cmd.append('-n')
            cmd.append(cenv)
            cmd = ' '.join(cmd)
            self.log(f"DDMD _set_env_vars for {cenv}: {cmd}")
            Exec(cmd, LocalExecInfo(env=self.mod_env,)).run()
        

    def start(self):
        """
        Launch an application. E.g., OrangeFS will launch the servers, clients,
        and metadata services on all necessary pkgs.

        :return: None
        """
        
        print("INFO: removing all previous runs")
        self.clean()

        if self.config['with_hermes'] == True:
            self._set_env_vars(self.hermes_env_vars)
        else:
            self._unset_vfd_vars(self.hermes_env_vars)

        # Check if all the OpenMM files exist
        if self._check_openmm() == False and self.config['skip_sim'] == True:
            print("ERROR: OpenMM files not found, cannot skip simulation")
            self.config['skip_sim'] = False
        
        iter_cnt = self.config['iter_count']
        
        total_start = time.time()
        
        for i in range(iter_cnt):
                            
            if self.config['skip_sim'] == False:
                start = time.time()
                self.openmm_list = self._run_openmm()
                # wait for all self.openmm_list to finish
                for task in self.openmm_list:
                    if task is not None:
                        task.wait()
                
                end = time.time()
            
                print(f"OpenMM[{(self.config['stage_idx'])}] : " + str(end - start) + " seconds")
            else:
                print("Skipping OpenMM stage")
            
            if self.config['short_pipe'] == False:
                start = time.time()
                self._run_aggregate()
                end = time.time()
                print(f"Aggregate[{(self.config['stage_idx'])}] : " + str(end - start) + " seconds")
                
            
            self.config['stage_idx']+=1
            
            train_start = time.time()
            self.train = self._run_train()
            if self.config['short_pipe'] == False:
                self.train.wait()
                end = time.time()
                print(f"Train[{(self.config['stage_idx'])}] : " + str(end - train_start) + " seconds")
            else:
                print("Shortened Pipeline: Train stage not waited")
            
            self.config['stage_idx']+=1
            
            start = time.time()
            self.inference = self._run_inference()
            end = time.time()
            
            if self.config['short_pipe'] == False:
                print(f"Inference stage[{(self.config['stage_idx'])}] : " + str(end - start) + " seconds")
            else:
                self.train.wait()
                end = time.time()
                print(f"Train[{(self.config['stage_idx']-1)}] and Inference[{(self.config['stage_idx'])}] : " + str(end - train_start) + " seconds")

        total_end = time.time()
        print(f"Total time: {total_end - total_start} seconds")
    
    
    def kill(self):
        """
        Kill a running application. E.g., OrangeFS will kill the servers,
        clients, and metadata services.

        :return: None
        """
        # FIXME: this will kill all python processes
        print("INFO: killing all python processes")
        Kill('python',
             PsshExecInfo(hostfile=self.hostfile,
                          env=self.env)).run()
        
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
        remove_paths = [
            "agent_runs", "inference_runs", "model_selection_runs",
            "aggregate_runs", "machine_learning_runs", "molecular_dynamics_runs"
        ]
        
        if self.config['skip_sim'] == True:
            print("INFO: do not clean OpenMM")
            # remove all paths excepts molecular_dynamics_runs
            for rp in remove_paths:
                if rp != "molecular_dynamics_runs":
                    remove_path = self.config['experiment_path'] + "/" + rp
                    print("INFO: removing " + remove_path)
                    Rm(remove_path).run()
        else:
            for rp in remove_paths:
                remove_path = self.config['experiment_path'] + "/" + rp
                print("INFO: removing " + remove_path)
                Rm(remove_path).run()

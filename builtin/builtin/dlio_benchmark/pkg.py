"""
This module provides classes and methods to launch the DlioBenchmark application.
DlioBenchmark is ....
"""
from jarvis_cd.core.pkg import Application, Color
from jarvis_cd.shell import Exec, MpiExecInfo, PsshExecInfo
from jarvis_cd.shell.process import Rm


class DlioBenchmark(Application):
    """
    This class provides methods to launch the DlioBenchmark application.
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
            # workload related configurations
            {
                'name': 'workload',  # The name of the parameter
                'msg': 'specify the workload name',  # Describe this parameter
                'type': str,  # What is the parameter type?
                'default': 'unet3d_a100',  # What is the default value if not required?
                'choices': [],
                'args': [],
            },
            {
                'name': 'generate_data',
                'msg': 'Does require to generate data before training?',
                'type': bool,
                'default': False,
                'choices': [],
                'args': [],
            },
            {
                'name': 'checkpoint_supported',
                'msg': 'Does the workload support checkpointing?',
                'type': bool,
                'default': True,
                'choices': [],
                'args': [],
            }, 
            {
                'name': 'checkpoint',
                'msg': 'Enable/disable checkpoint',
                'type': bool,
                'default': True,
                'choices': [],
                'args': [],
            }, 
            # dataset related configurations
            {
                'name': 'data_path',
                'msg': 'The path of the dataset',
                'type': str,
                'default': None,
                'choices': [],
                'args': [],
            },
            {
                'name': 'num_files_train',
                'msg': 'Number of files used for training',
                'type': int,
                'default': None,
                'choices': [],
                'args': [],
            },
            # reader related configurations
            {
                'name': 'batch_size',
                'msg': 'Number of samples read per iteration',
                'type': int,
                'default': None,
                'choices': [],
                'args': [],
            },
            {
                'name': 'read_threads',
                'msg': 'Number of read threads in dataloader',
                'type': int,
                'default': None,
                'choices': [],
                'args': [],
            }, 
            # train related configurations
            {
                'name': 'epochs',
                'msg': 'Number of epochs to run',
                'type': int,
                'default': None,
                'choices': [],
                'args': [],
            },
            # checkpoint related configurations
            {
                'name': 'checkpoint_path',
                'msg': 'Path of the checkpoint files',
                'type': str,
                'default': None,
                'choices': [],
                'args': [],
            }, 
            {
                'name': 'checkpoint_after_epoch',
                'msg': 'Checkpoint after the specified epoch id',
                'type': int,
                'default': None,
                'choices': [],
                'args': [],
            }, 
            {
                'name': 'epochs_between_checkpoints',
                'msg': 'Checkpoint interval (unit: epochs)',
                'type': int,
                'default': None,
                'choices': [],
                'args': [],
            }, 
            # process related configuration
            {
                'name': 'nprocs',
                'msg': 'Number of processes',
                'type': int,
                'default': 8,
            },
            {
                'name': 'ppn',
                'msg': 'The number of processes per node',
                'type': int,
                'default': 8,
            },
            # Run with tracing or not
            {
                'name': 'tracing',
                'msg': 'Enable/disable tracing (running with/without DFTracer)',
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
        # reconfigure data_path
        if self.config['data_path'] is None:
            self.config['data_path'] = f"data/{self.config['workload']}"
        elif f"data/{self.config['workload']}" not in self.config['data_path']:
            self.config['data_path'] = f"{self.config['data_path']}/data/{self.config['workload']}"  

        # reconfigure checkpoint path
        if self.config['checkpoint_supported']:
            if self.config['checkpoint_path'] is None:
                self.config['checkpoint_path'] = f"checkpoints/{self.config['workload']}"
            elif f"checkpoints/{self.config['workload']}" not in self.config['checkpoint_path']:
                self.config['checkpoint_path'] = f"{self.config['checkpoint_path']}/checkpoints/{self.config['workload']}" 

    def start(self):
        """
        Launch an application. E.g., OrangeFS will launch the servers, clients,
        and metadata services on all necessary pkgs.

        :return: None
        """
        
        # step1: generate data if it is required before training
        if self.config['generate_data']:
            # construct the command
            gen_cmd = [
                'dlio_benchmark',
                f'workload={self.config['workload']}',
                f'++workload.workflow.generate_data=True',
                f'++workload.workflow.train=False',
                f'++workload.dataset.data_folder={self.config['data_path']}' 
            ]

            if self.config['num_files_train'] is not None:
                gen_cmd.append(f'++workload.dataset.num_files_train={self.config['num_files_train']}')

            # run the command to generate data
            Exec(' '.join(gen_cmd),
                MpiExecInfo(env=self.mod_env,
                            hostfile=self.hostfile,
                            nprocs=self.config['nprocs'],
                            ppn=self.config['ppn'])).run()

        # step2: clear the system cache
        Exec('sudo drop_caches',
             PsshExecInfo(env=self.env,
                        hostfile=self.hostfile)).run()
        
        # step3: run the benchmark with the workload
        if self.config['tracing']:
            self.mod_env['DFTRACER_ENABLE'] = '1'
            self.mod_env['DFTRACER_INC_METADATA'] = '1'   

        run_cmd = [
            'dlio_benchmark',
            f'workload={self.config['workload']}',
            f'++workload.workflow.generate_data=False',
            f'++workload.workflow.train=Train',
            f'++workload.dataset.data_folder={self.config['data_path']}'  
        ]

        if self.config['num_files_train'] is not None:
            run_cmd.append(f'++workload.dataset.num_files_train={self.config['num_files_train']}')
        
        if self.config['batch_size'] is not None:
            run_cmd.append(f'++workload.reader.batch_size={self.config['batch_size']}')
        
        if self.config['read_threads'] is not None:
            run_cmd.append(f'++workload.reader.read_threads={self.config['read_threads']}')

        if self.config['epochs'] is not None:
            run_cmd.append(f'++workload.train.epochs={self.config['epochs']}')
        
        if self.config['checkpoint_supported']:
            run_cmd.append(f'++workload.workflow.checkpoint={self.config['checkpoint']}')
            run_cmd.append(f'++workload.checkpoint.checkpoint_folder={self.config['checkpoint_path']}')
            if self.config['checkpoint_after_epoch'] is not None:
                run_cmd.append(f'++workload.checkpoint.checkpoint_after_epoch={self.config['checkpoint_after_epoch']}')
            if self.config['epochs_between_checkpoints'] is not None:
                run_cmd.append(f'++workload.checkpoint.epochs_between_checkpoints={self.config['epochs_between_checkpoints']}') 
        #print(f"self.env = {self.env}", flush=True)
        # run the benchmark command
        Exec(' '.join(run_cmd),
             MpiExecInfo(env=self.mod_env,
                         hostfile=self.hostfile,
                         nprocs=self.config['nprocs'],
                         ppn=self.config['ppn'])).run()
        

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
        # clear data path
        Rm(self.config['data_path'] + '*',
           PsshExecInfo(env=self.env,
                        hostfile=self.hostfile)).run()

        self.log(f'Removing dataset {self.config['data_path']}', Color.YELLOW)

        # clear checkpoint
        Rm(self.config['checkpoint_path'] + '*',
           PsshExecInfo(env=self.env,
                        hostfile=self.hostfile)).run()
        
        self.log(f'Removing checkpoints {self.config['checkpoint_path']}', Color.YELLOW)

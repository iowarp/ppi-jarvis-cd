"""
This module provides classes and methods to launch the NyxLya application.
NyxLya is ....
"""
from jarvis_cd.core.pkg import Application
from jarvis_cd.shell import Exec, MpiExecInfo, PsshExecInfo
from jarvis_cd.shell.process import Mkdir, Rm


class NyxLya(Application):
    """
    This class provides methods to launch the NyxLya application.
    """
    def _init(self):
        """
        Initialize paths
        """
        self.inputs_path = f'{self.pkg_dir}/config/inputs'
        self.nyx_lya_path = None

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
                'msg': 'Processes per pkg',
                'type': int,
                'default': 1,
            },
            {
                'name': 'nyx_install_path',
                'msg': 'Absolute path to Nyx installation',
                'type': str,
                'default': None,
            },
            {
                'name': 'initial_z',
                'msg': 'final value of z, z corresponds to a time stemp (e.g., 190.0)',
                'type': float,
                'default': 159.0,
            },
            {
                'name': 'final_z',
                'msg': 'final value of z, z corresponds to a time stemp (e.g., 180.0). final_z < initial_z',
                'type': float,
                'default': 2.0, 
            },
            {
                'name': 'plot_z_values',
                'msg': 'z values to save the plot files(e.g., "188.0 186.0 184.0 182.0")',
                'type': str,
                'default': "7.0 6.0 5.0 4.0 3.0 2.0",
            },
            {
                'name': 'particle_file',
                'msg': 'Absolute path to the binary particle fileoutput(e.g., 64sssss_20mpc.nyx)',
                'type': str,
                'default': '64sssss_20mpc.nyx',
            },
            {
                'name': 'output',
                'msg': 'Absolute path to the output directory',
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
        if self.config['nyx_install_path'] is None:
            print("Error: please provide the path to Nyx installation....")
            exit(1)
        else:
            self.nyx_lya_path = f"{self.config['nyx_install_path']}/LyA"

        if self.config['particle_file'] == "64sssss_20mpc.nyx":
            self.config['particle_file'] = f'{self.nyx_lya_path}/64sssss_20mpc.nyx'
        
        if self.config['output'] is None:
            self.config['output'] = f'{self.nyx_lya_path}/outputs'
            Mkdir(self.config['output'], PsshExecInfo(hostfile=self.hostfile,
                                          env=self.env)).run()

        # copy a template inputs file from NYX installation path to the pkg directory
        self.copy_template_file(f'{self.nyx_lya_path}/inputs', self.inputs_path)
        # modify the inputs file based on user's input
        self._configure_nyx()

    def _configure_nyx(self):

        prefix_mapping = {
            'nyx.write_hdf5': f"",
            'nyx.initial_z': f"nyx.initial_z = {self.config['initial_z']}\n",
            'nyx.final_z': f"nyx.final_z = {self.config['final_z']}\n",
            'amr.plot_file': f"amr.plot_file = {self.config['output']}/plt\n",
            'nyx.plot_z_values': f"nyx.plot_z_values = {self.config['plot_z_values']}\n",
            'nyx.binary_particle_file': f"nyx.binary_particle_file = {self.config['particle_file']}\n",
            'amr.check_file': f"amr.check_file = {self.config['output']}/chk\n",
            'amr.derive_plot_vars': lambda line: f"#{line}",
            'amr.data_log': f"amr.data_log = {self.config['output']}/runlog\n",
            'amr.grid_log': f"amr.grid_log = {self.config['output']}/grdlog\n",
        }

        lines = []
        lines.append("nyx.write_hdf5 = 1\n")
        with open(self.inputs_path, 'r') as file:
            for line in file:
                line_stripped = line.strip()
                action = prefix_mapping.get(line_stripped.split(' ')[0], None)
                
                if action == None:
                    lines.append(line)
                elif callable(action):
                    lines.append(action(line))
                else:
                    lines.append(action)
        
        # rewrite the file
        with open(self.inputs_path, 'w') as file:
            file.writelines(lines)

    def start(self):
        """
        Launch an application. E.g., OrangeFS will launch the servers, clients,
        and metadata services on all necessary pkgs.

        :return: None
        """
        # since "self.nyx_lya_path" is always set to be none in _init(), we need to rest it here
        self.nyx_lya_path = f"{self.config['nyx_install_path']}/LyA"
        Exec(f'{self.nyx_lya_path}/nyx_LyA {self.inputs_path}',
             MpiExecInfo(nprocs=self.config['nprocs'],
                         ppn=self.config['ppn'],
                         hostfile=self.hostfile,
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
        output_dir = self.config['output'] + "*"
        print(f'Removing {output_dir}')
        Rm(output_dir).run()

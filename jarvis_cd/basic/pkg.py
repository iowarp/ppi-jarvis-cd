"""
This module contains abstract base classes which represent the different
pkg types in Jarvis.
"""

from abc import ABC, abstractmethod
from jarvis_cd.basic.jarvis_manager import JarvisManager
from jarvis_util.util.logging import ColorPrinter, Color
from jarvis_util.util.naming import to_snake_case
from jarvis_util.serialize.yaml_file import YamlFile
from jarvis_util.shell.local_exec import LocalExecInfo
from jarvis_util.shell.exec import Exec
from jarvis_util.util.argparse import ArgParse
from jarvis_util.jutil_manager import JutilManager
from jarvis_util.shell.filesystem import Mkdir, Rm
from jarvis_util.shell.pssh_exec import PsshExecInfo
import yaml
import inspect
import pathlib
import shutil
import math
import os
import time
import pandas as pd


class PkgArgParse(ArgParse):
    def define_options(self):
        self.add_cmd()
        self.add_args(self.custom_info['menu'])

    def main_menu(self):
        pass


class PipelineZip:
    """
    A class to represent a zip of pipeline configurations
    """
    def __init__(self):
        self.zip = []
        self.zip_len = 0

    def add_param_set(self, pkg, var_name, var_vals):
        self.zip_len = len(var_vals)
        self.zip.append((pkg, var_name, var_vals))


class PipelineIterator:
    """
    Grid searching pipeline parameters
    """
    def __init__(self, ppl):
        """
        Initialize grid search

        fors: A list of lists [(pkg, var_name, var_vals)]
        """
        self.ppl = ppl
        self.norerun = set()
        if 'norerun' in ppl.config['iterator']:
            self.norerun = set(ppl.config['iterator']['norerun'])
        self.fors = []
        self.cur_iters = []
        self.cur_pos = []
        self.cur_pos_diff = []
        self.iter_count = 0
        self.max_iter_count = 0
        self.conf_dict = {}
        self.linear_conf_dict = {}
        self.iter_vars = ppl.config['iterator']['vars']
        self.iter_loop = ppl.config['iterator']['loop']
        self.repeat = ppl.config['iterator']['repeat']
        ppl.set_config_env_vars()
        self.iter_out = os.path.expandvars(ppl.config['iterator']['output'])
        print(f'ITER OUT: {self.iter_out} '
              f"(from: {ppl.config['iterator']['output']})")
        self.stats_path = f'{self.iter_out}/stats_dict.csv'
        self.stats = []

        Mkdir(self.iter_out)
        self.iter_vars = self.iter_vars
        for zip_set in self.iter_loop:
            self.add_for()
            for zip_name in zip_set:
                pkg_name, var_name = zip_name.split('.')
                pkg = ppl.sub_pkgs_dict[pkg_name]
                self.add_to_for_zip(pkg, var_name, self.iter_vars[zip_name])

    def add_for(self):
        self.fors.append(PipelineZip())

    def add_to_for_zip(self, pkg, var_name, var_vals):
        for_zip = self.fors[-1]
        for_zip.add_param_set(pkg, var_name, var_vals)
        self.conf_dict[pkg] = {}

    def begin(self):
        for i in range(len(self.fors)):
            self.cur_iters.append(iter(range(self.fors[i].zip_len)))
            self.cur_pos.append(next(self.cur_iters[i]))
        self.cur_pos_diff = [1] * len(self.cur_pos)
        self.conf_dict = self.current()
        self.iter_count = 0
        self.max_iter_count = math.prod([for_zip.zip_len for for_zip
                                         in self.fors])
        return self.conf_dict

    def current(self):
        for i in range(len(self.cur_iters)):
            for pkg, var_name, var_vals in self.fors[i].zip:
                self.conf_dict[pkg][var_name] = var_vals[self.cur_pos[i]]
                pkg.iter_diff = self.cur_pos_diff[i]
        for pkg, conf in self.conf_dict.items():
            for key, val in conf.items():
                self.linear_conf_dict[f'{pkg.pkg_id}.{key}'] = val
        return self.conf_dict

    def next(self):
        self.cur_pos_diff = [0] * len(self.cur_pos)
        for i in range(len(self.cur_iters) - 1, -1, -1):
            try:
                self.cur_pos[i] = next(self.cur_iters[i])
                self.cur_pos_diff[i] = 1
                break
            except StopIteration:
                if i == 0:
                    return None
                else:
                    self.cur_iters[i] = iter(range(self.fors[i].zip_len))
                    self.cur_pos[i] = next(self.cur_iters[i])
                    self.cur_pos_diff[i] = 1
        conf_dict = self.current()
        self.iter_count += 1
        return conf_dict

    def config_pkgs(self, conf_dict):
        for pkg, conf in conf_dict.items():
            pkg.skip_run = False
            if pkg.pkg_id in self.norerun and pkg.iter_diff == 0:
                pkg.skip_run = True
            pkg.set_config_env_vars()
            pkg.configure(**conf)
            pkg.save()

    def save_run(self, conf_dict):
        if conf_dict:
            print('WARNING: conf_dict is defined but not used.')
        stat_dict = {**self.linear_conf_dict}
        # Get the package-specific stats
        for pkg in self.ppl.sub_pkgs:
            if hasattr(pkg, '_get_stat'):
                pkg._get_stat(stat_dict)
        # Save the stats to the list
        self.stats.append(stat_dict)
        df = pd.DataFrame(self.stats)
        df.to_csv(self.stats_path, index=False)

    def analysis(self):
        for pkg in self.ppl.sub_pkgs:
            if hasattr(pkg, '_analysis'):
                pkg._analysis(self.stats)
        df = pd.DataFrame(self.stats)
        df.to_csv(self.stats_path, index=False)

class Pkg(ABC):
    """
    Represents a generic Jarvis pkg. Includes methods to load configurations
    and to specialize the pkg using a global_id.
    """

    def __init__(self):
        """
        Initialize paths
        
        jarvis: the JarvisManager singleton
        jutil: the JutilManager singleton
        pkg_type: the type of this package (semantic string)
        root: the root package of this package
        global_id: the unique identifier for this package (dot-separated string)
        pkg_id: the semantic name of this package (last part of globl_id)
        pkg_dir: the code's source directory
        config_dir: the directory where configuration data is stored
        private_dir: the directory where private data is stored
        shared_dir: the directory where shared data is stored
        config_path: the path to the configuration file
        config: the configuration data
        sub_pkgs: the sub-packages of this package (ordered list)
        sub_pkgs_dict: the sub-packages of this package (dict)
        env_path: the path to the environment file
        env: the environment data
        mod_env: the environment data + LD_PRELOAD
        iter_vars: the iteration variables
        iter_loop: the iteration loop
        iter_out: the iteration output
        stats_path: the path to the statistics file
        stats: the statistics list
        """
        self.jarvis = JarvisManager.get_instance()
        self.jutil = JutilManager.get_instance()
        self.pkg_type = to_snake_case(self.__class__.__name__)
        self.root = None
        self.global_id = None
        self.pkg_id = None
        """The pkg dir (e.g., ${JARVIS_ROOT}/builtin/orangefs)"""
        self.pkg_dir = str(
            pathlib.Path(inspect.getfile(self.__class__)).parent.resolve())
        self.config_dir = None
        self.private_dir = None
        self.shared_dir = None
        self.config_path = None
        self.config = None
        self.sub_pkgs = []
        self.sub_pkgs_dict = {}
        self.interceptors_dict = {}
        self.env_path = None
        self.env = None
        self.mod_env = None
        self.iterator = None
        self.exit_code = 0
        self.start_time = 0
        self.stop_time = 0
        self.skip_run = False

    def log(self, msg, color=None):
        ColorPrinter.print(msg, color)

    def _init_common(self, global_id, root):
        """
        Update paths in this package based on the global_id

        :param global_id: The unique identifier for this package
        :return: None
        """
        if root is None:
            root = self
        self.root = root
        self.global_id = self._get_global_id(global_id)
        id_split = self.global_id.split('.')
        self.pkg_id = id_split[-1]
        relpath = self.global_id.replace('.', '/')
        self.config_dir = f'{self.jarvis.config_dir}/{relpath}'
        self.private_dir = f'{self.jarvis.private_dir}/{relpath}'
        if self.jarvis.shared_dir is not None:
            self.shared_dir = f'{self.jarvis.shared_dir}/{relpath}'
        self.config_path = f'{self.config_dir}/{self.pkg_id}.yaml'
        if len(id_split) > 1:
            self.env_path = None
        else:
            self.env_path = f'{self.config_dir}/env.yaml'

    def _get_global_id(self, global_id):
        if global_id is None:
            global_id = self.jarvis.cur_pipeline
        if global_id is None:
            raise Exception('No pipeline currently selected')
        return global_id

    def create(self, global_id):
        """
        Create a new pkg and its filesystem data

        :param global_id: A dot-separated, globally unique identifier for
        this pkg. Indicates where configuration data is stored.
        :return: self
        """
        self._init_common(global_id, self.root)
        if os.path.exists(self.config_path):
            self.load(global_id, self.root)
            return self
        self.config = {
            'sub_pkgs': [],
            'interceptors': {}
        }
        self.sub_pkgs = []
        self.interceptors_dict = {}
        self.env_path = f'{self.config_dir}/env.yaml'
        if self.env is None:
            self.env = {}
        os.makedirs(self.config_dir, exist_ok=True)
        if self.shared_dir is not None:
            os.makedirs(self.shared_dir, exist_ok=True)
        self._init()
        return self

    def load(self, global_id=None, root=None, with_config=True):
        """
        Load the configuration of a pkg from the filesystem. Will
        create if it doesn't already exist.

        :param global_id: A dot-separated, globally unique identifier for
        this pkg. Indicates where configuration data is stored.
        :param root: The parent package
        :param with_config: Whether to load pkg configurations
        :return: self
        """
        self._init_common(global_id, root)
        if self.env_path is not None and os.path.exists(self.env_path):
            self.env = YamlFile(self.env_path).load()
        elif self.root is not None:
            self.env = self.root.env
        if not os.path.exists(self.config_path):
            return self.create(global_id)
        if not with_config:
            return self
        self.config = YamlFile(self.config_path).load()
        
        # Ensure interceptors is initialized as a dictionary if not present
        if 'interceptors' not in self.config:
            self.config['interceptors'] = {}
            
        # Initialize interceptors_dict for constructed packages
        if not hasattr(self, 'interceptors_dict'):
            self.interceptors_dict = {}
            
        # Reconstruct interceptor packages from saved config (only for pipelines, not individual packages)
        if self.__class__.__name__ == 'Pipeline' and isinstance(self.config['interceptors'], dict):
            for interceptor_name, interceptor_config in self.config['interceptors'].items():
                # Extract the interceptor type from the config
                if 'pkg_type' in interceptor_config:
                    interceptor_type = interceptor_config['pkg_type']
                else:
                    # For backward compatibility, try to infer from name
                    interceptor_type = interceptor_name
                    
                interceptor_pkg = self.jarvis.construct_pkg(interceptor_type)
                if interceptor_pkg is None:
                    self.log(f'Could not find interceptor pkg: {interceptor_type}. Skipping.',
                             Color.RED)
                    continue
                    
                global_id = f'{self.global_id}.{interceptor_name}'
                interceptor_pkg.load(global_id, self.root)
                
                # Configure the interceptor with saved parameters (exclude internal config keys)
                internal_keys = {'pkg_type', 'sub_pkgs', 'interceptors'}
                saved_config = {k: v for k, v in interceptor_config.items() if k not in internal_keys}
                if saved_config:  # Only configure if there are parameters
                    interceptor_pkg.configure(**saved_config)
                
                # Store the constructed package
                self.interceptors_dict[interceptor_name] = interceptor_pkg
        
        for sub_pkg_type, sub_pkg_id in self.config['sub_pkgs']:
            sub_pkg = self.jarvis.construct_pkg(sub_pkg_type)
            if sub_pkg is None:
                self.log(f'Could not find pkg: {sub_pkg_type}. Skipping.',
                         Color.RED)
                continue
            sub_pkg.load(f'{self.global_id}.{sub_pkg_id}', self.root)
            self.sub_pkgs.append(sub_pkg)
            self.sub_pkgs_dict[sub_pkg.pkg_id] = sub_pkg
        
        # For non-Pipeline packages, ensure mod_env is initialized and process interceptors
        if self.__class__.__name__ != 'Pipeline':
            # Initialize mod_env if not already set
            if not hasattr(self, 'mod_env') or self.mod_env is None:
                self.mod_env = self.env.copy() if self.env else {}
            
            # If this package has interceptors configured, apply them
            if 'interceptors' in self.config and self.config['interceptors'] and isinstance(self.config['interceptors'], list):
                self._process_interceptors()
        
        self._init()
        return self

    def save(self):
        """
        Save a pkg and its sub-pkgs
        :return: Self
        """
        self.config['pkg_type'] = self.pkg_type
        YamlFile(self.config_path).save(self.config)
        if self.env_path is not None:
            YamlFile(self.env_path).save(self.env)
        for pkg in self.sub_pkgs:
            pkg.save()
        return self

    def set_config_env_vars(self, cur_iter_temp=None):
        if cur_iter_temp is not None:
            os.environ['ITER_DIR'] = cur_iter_temp
        os.environ['SHARED_DIR'] = self.shared_dir
        os.environ['PRIVATE_DIR'] = self.private_dir
        os.environ['CONFIG_DIR'] = self.config_dir

    def clear(self):
        """
        Destroy a pipeline's sub-pkgs

        :return: self
        """
        self.reset()
        return self

    def reset(self):
        """
        Destroy a pipeline's sub-pkgs

        :return: self
        """
        try:
            for dir_name in os.listdir(self.config_dir):
                path = os.path.join(self.config_dir, dir_name)
                if os.path.isdir(path):
                    shutil.rmtree(path)
            os.remove(self.config_path)
            self.create(self.global_id)
        except FileNotFoundError:
            pass
        return self

    def get_path(self, config=False, shared=False, private=False, pkg=False):
        if shared:
            return self.shared_dir
        if private:
            return self.private_dir
        if config:
            return self.config_dir
        raise Exception('Config, shared, and private were all false')

    def destroy(self):
        """
        Destroy a pipeline and its sub-pkgs

        :return: None
        """
        for pkg in self.sub_pkgs:
            if pkg is not None:
                pkg.destroy()
        try:
            shutil.rmtree(self.config_dir)
        except FileNotFoundError:
            pass

    def insert(self, at_id, pkg_type, pkg_id=None, do_configure=True, **kwargs):
        """
        Create and append a pkg to the pipeline

        :param at_id: The id of the pkg to insert at
        :param pkg_type: The type of pkg to create (e.g., OrangeFS)
        :param pkg_id: Semantic name of the pkg to create
        :param do_configure: Whether to configure while appending
        :param kwargs: Any parameters the user want to configure in the pkg
        :return: self
        """
        if pkg_id is None:
            pkg_id = self._make_unique_name(pkg_type)
        off = 0
        if at_id is None or len(self.config['sub_pkgs']) == 0:
            self.config['sub_pkgs'].append([pkg_type, pkg_id])
            off = len(self.config['sub_pkgs'])
        else:
            if isinstance(at_id, int):
                off = at_id
            else:
                for sub_pkg_id in self.config['sub_pkgs']:
                    if sub_pkg_id == at_id:
                        break
                    off += 1
            self.config['sub_pkgs'].insert(off, [pkg_type, pkg_id])
        pkg = self.jarvis.construct_pkg(pkg_type)
        if pkg is None:
            raise Exception(f'Could not find pkg: {pkg_type}')
        global_id = f'{self.global_id}.{pkg_id}'
        pkg._init_common(global_id, self.root if self.root else self)
        if os.path.exists(pkg.config_path):
            pkg.load(global_id, self.root if self.root else self)
        else:
            pkg.config = {
                'sub_pkgs': [],
                'interceptors': {}
            }
            pkg.sub_pkgs = []
            pkg.interceptors_dict = {}
            pkg.env_path = f'{pkg.config_dir}/env.yaml'
            if pkg.env is None:
                pkg.env = {}
            os.makedirs(pkg.config_dir, exist_ok=True)
            if pkg.shared_dir is not None:
                os.makedirs(pkg.shared_dir, exist_ok=True)
            pkg._init()
        if do_configure:
            pkg.update_env(self.env)
            pkg.configure(**kwargs)
        self.sub_pkgs.insert(off, pkg)
        self.sub_pkgs_dict[pkg.pkg_id] = pkg
        return self

    def append(self, pkg_type, pkg_id=None, do_configure=True, **kwargs):
        """
        Create and append a pkg to the pipeline

        :param pkg_type: The type of pkg to create (e.g., OrangeFS)
        :param pkg_id: Semantic name of the pkg to create
        :param do_configure: Whether to configure while appending
        :param kwargs: Any parameters the user want to configure in the pkg
        :return: self
        """
        return self.insert(None, pkg_type, pkg_id, do_configure, **kwargs)

    def add_interceptor(self, pkg_name, interceptor_pkg):
        """
        Add an interceptor package configuration and constructed package
        
        :param pkg_name: The name/key for the interceptor
        :param interceptor_pkg: The constructed interceptor package object
        :return: self
        """
        if 'interceptors' not in self.config:
            self.config['interceptors'] = {}
        
        # Store the interceptor's configuration parameters in self.config
        interceptor_config = interceptor_pkg.config.copy()
        interceptor_config['pkg_type'] = interceptor_pkg.pkg_type
        self.config['interceptors'][pkg_name] = interceptor_config
        
        # Store the constructed package object separately
        self.interceptors_dict[pkg_name] = interceptor_pkg
        return self

    def prepend(self, pkg_type, pkg_id=None, do_configure=True, **kwargs):
        """
        Create and append a pkg to the pipeline

        :param pkg_type: The type of pkg to create (e.g., OrangeFS)
        :param pkg_id: Semantic name of the pkg to create
        :param do_configure: Whether to configure while appending
        :param kwargs: Any parameters the user want to configure in the pkg
        :return: self
        """
        return self.insert(0, pkg_type, pkg_id, do_configure, **kwargs)

    def _make_unique_name(self, pkg_type):
        if self.get_pkg(pkg_type) is None:
            return pkg_type
        count = 1
        while True:
            new_name = f'{pkg_type}{count}'
            if self.get_pkg(new_name) is not None:
                count += 1
            return new_name

    def remove(self, pkg_id):
        """
        Remove a pkg from the pipeline & delete its contents

        :param pkg_id: The name of the pkg to remove
        :return: self
        """
        pkg = self.get_pkg(pkg_id)
        if pkg:
            pkg.destroy()
        self.unlink(pkg_id)
        return self

    def unlink(self, pkg_id):
        """
        Remove a pkg from the pipeline, but keep its contents in case
        it gets added back.

        :param pkg_id: The name of the pkg to remove
        :return: self
        """
        self.sub_pkgs = [test_pkg for test_pkg in self.sub_pkgs
                          if test_pkg.pkg_id != pkg_id]
        self.config['sub_pkgs'] = [
            [test_pkg_type, test_pkg_id]
            for test_pkg_type, test_pkg_id in self.config['sub_pkgs']
            if test_pkg_id != pkg_id]
        return self

    def get_pkg(self, pkg_id):
        """
        Get a pkg in the pipeline.

        :param pkg_id: The pkg id to find
        :return: A pkg
        """
        matches = [pkg for pkg in self.sub_pkgs if pkg.pkg_id == pkg_id]
        if len(matches) == 0:
            return None
        else:
            return matches[0]

    def view_pkgs(self):
        print(self.to_string_pretty())

    def env_show(self):
        print(yaml.dump(self.env))

    def update_env(self, env):
        """
        Update the current environment for this program

        :param env: The environment dict
        :return:
        """
        env.update(self.env)
        self.env = env
        
        # Create mod_env as a copy of env, but preserve any existing mod_env-specific variables
        new_mod_env = env.copy()
        if hasattr(self, 'mod_env') and self.mod_env:
            # Preserve LD_PRELOAD and other mod_env-specific variables
            mod_env_keys = {'LD_PRELOAD'}
            for key in mod_env_keys:
                if key in self.mod_env and key not in new_mod_env:
                    new_mod_env[key] = self.mod_env[key]
                elif key in self.mod_env and self.mod_env[key] != new_mod_env.get(key, ''):
                    # Merge if both exist and are different
                    new_mod_env[key] = self.mod_env[key]
        self.mod_env = new_mod_env

    @staticmethod
    def _track_env(env, env_track_dict=None):
        """
        Add and remove cached environment variables.

        :param env_track_dict: a dict of booleans or strings. Boolean indicates
        whether to track the environment variable, which are the keys
        of the dict. String indicates track the variable and set to this value.
        :return: None
        """
        if env_track_dict is None:
            return env
        for key, val in env_track_dict.items():
            if isinstance(val, str):
                env[key] = val
                continue
            if val:
                if key in os.environ:
                    env[key] = os.getenv(key)
                else:
                    env[key] = ''
            else:
                if key in env:
                    del env[key]
        return env

    def track_env(self, env_track_dict=None):
        """
        Add and remove cached environment variables.

        :param env_track_dict: a dict of booleans or strings. Boolean indicates
        whether to track the environment variable, which are the keys
        of the dict. String indicates track the variable and set to this value.
        :return: self
        """
        self.env = self._track_env(self.env, env_track_dict)
        return self

    def scan_env(self, rescan_list=None):
        """
        Re-scan environment variables.

        :param rescan_list: a list of keys to re-scan.
        :return: self
        """
        if rescan_list is None:
            rescan_list = list(self.env.keys())
        for key in rescan_list:
            self.env[key] = os.getenv(key)
        return self

    def prepend_env(self, env_var, path):
        """
        Prepend a path to the an environment variable, such as LD_PRELOAD.

        :param env_var: The name of the environment variable
        :param path: The path to prepend
        :return:
        """
        if env_var == 'LD_PRELOAD':
            env = self.mod_env
        else:
            env = self.env
        if env_var in env:
            cur_env = env[env_var]
        else:
            cur_env = os.getenv(env_var)

        if cur_env is None or len(cur_env) == 0:
            env[env_var] = path
        else:
            env[env_var] = f'{path}:{cur_env}'

    def append_env(self, env_var, path):
        """
        Append a path to the an environment variable, such as LD_PRELOAD.

        :param env_var: The name of the environment variable
        :param path: The path to prepend
        :return:
        """
        if env_var == 'LD_PRELOAD':
            env = self.mod_env
        else:
            env = self.env
        if env_var in env:
            cur_env = env[env_var]
        else:
            cur_env = os.getenv(env_var)

        if cur_env is None or len(cur_env) == 0:
            env[env_var] = path
        else:
            env[env_var] = f'{cur_env}:{path}'

    def setenv(self, env_var, val):
        """
        Set the Jarvis environment variable

        :param env_var: The environment variable
        :param val: The value of the environment variable
        :return:
        """
        self.env[env_var] = val

    def find_library(self, lib_name, env_vars=None):
        """
        Find the location of a shared object automatically using environment
        variables. If None, will search LD_LIBRARY_PATH.

        :param lib_name: The library to search for. We will search for
        any file matching lib{lib_name}.so and {lib_name}.so.
        :param env_vars: A list of environment variables to search for or
        a string for a single variable.
        :return: string or None
        """
        name_opts = [
            f'{lib_name}.so',
            f'lib{lib_name}.so',
        ]
        for name in name_opts:
            exe = Exec(f'cc -print-file-name={name}',
                        LocalExecInfo(env=self.env,
                                      hide_output=True,
                                      collect_output=True))
            res = exe.stdout['localhost'].strip()
            if len(res) and res != name:
                return res
        if env_vars is None:
            env_vars = ['LD_LIBRARY_PATH']

        for env_var in env_vars:
            if env_var not in self.env:
                continue
            paths = self.env[env_var].split(':')
            for path in paths:
                if not os.path.exists(path):
                    continue
                filenames = os.listdir(path)
                for name_opt in name_opts:
                    if name_opt in filenames:
                        return f'{path}/{name_opt}'
        return None

    def __str__(self):
        return self.to_string_pretty()

    def __repr__(self):
        return self.to_string_pretty()

    def to_string_pretty(self):
        return '\n'.join(self.to_string_list_pretty())

    def to_string_list_pretty(self, depth=0):
        space = ' ' * depth
        info = [f'{space}{self.pkg_type} with name {self.pkg_id}']
        for key, val in self.config.items():
            if key == 'sub_pkgs':
                continue
            info.append(f'{space}  {key}={val}')
        for sub_pkg in self.sub_pkgs:
            info += sub_pkg.to_string_list_pretty(depth + 2)
        return info

    @abstractmethod
    def _init(self):
        """
        Initialize variables global to the project.
        Called after load() and create()

        :return:
        """
        pass


class SimplePkg(Pkg):
    """
    A SimplePkg represents a single program. A pipeline is not a SimplePkg
    because it represents a combination of multiple programs.
    """

    def configure_menu(self):
        """
        Add some common configuration options used across all CLI menus.

        :return:
        """
        menu = self._configure_menu()
        menu += [
            {
                'name': 'sleep',
                'msg': 'How much time to sleep during start (seconds)',
                'type': int,
                'default': 0,
            },
            {
                'name': 'reinit',
                'msg': 'Destroy previous configuration and rebuild',
                'type': bool,
                'default': False
            },
            {
                'name': 'do_dbg',
                'msg': 'Enable or disable debugging',
                'type': bool,
                'default': False
            },
            {
                'name': 'dbg_port',
                'msg': 'The port to use for debugging',
                'type': int,
                'default': 4000
            },
            {
                'name': 'stdout',
                'msg': 'The file to use for holding output. Use stderr to'
                       'pipe to the same file as stderr.',
                'type': str,
                'default': None
            },
            {
                'name': 'stderr',
                'msg': 'The file to use for holding error output. Use stdout '
                       'to pipe to the same file as stdout.',
                'type': str,
                'default': None
            },
            {
                'name': 'hide_output',
                'msg': 'Hide output of the runtime.',
                'type': bool,
                'default': False
            },
            {
                'name': 'interceptors',
                'msg': 'A list of interceptor package names',
                'type': list,
                'args': [
                    {
                        'name': 'interceptor',
                        'msg': 'A string representing an interceptor package name',
                        'type': str,
                    }
                ]
            }
        ]
        return menu

    @abstractmethod
    def _configure_menu(self):
        """
        Create a CLI menu for the configurator method.
        For thorough documentation of these parameters, view:
        https://github.com/scs-lab/jarvis-util/wiki/3.-Argument-Parsing

        :return: List(dict)
        """
        return []

    def configure(self, **kwargs):
        if 'reinit' not in kwargs:
            kwargs['reinit'] = False
        if 'stdout' not in kwargs:
            kwargs['stdout'] = None
        if 'stderr' not in kwargs:
            kwargs['stderr'] = None
        if kwargs['stdout'] == 'stderr':
            kwargs['stdout'] = kwargs['stderr']
        if kwargs['stderr'] == 'stdout':
            kwargs['stderr'] = kwargs['stdout']
        self.update_config(kwargs, rebuild=kwargs['reinit'])
        self._configure(**kwargs)
        self._process_interceptors()

    @abstractmethod
    def _configure(self, **kwargs):
        """
        Converts the Jarvis configuration to application-specific configuration.
        E.g., OrangeFS produces an orangefs.xml file.

        :param kwargs: The human-readable jarvis YAML configuration for the
        application.
        :return: None
        """
        pass

    def _process_interceptors(self):
        """
        Process the interceptors list and call modify_env() on each interceptor.
        
        :return: None
        """
        if 'interceptors' not in self.config or not self.config['interceptors']:
            return
            
        # Access the root pipeline to get constructed interceptor packages
        if self.root and hasattr(self.root, 'interceptors_dict'):
            root_interceptors = self.root.interceptors_dict
            
            for interceptor_name in self.config['interceptors']:
                if interceptor_name in root_interceptors:
                    interceptor_pkg = root_interceptors[interceptor_name]
                    if hasattr(interceptor_pkg, 'modify_env'):
                        # Update interceptor's environment with the environment pointer
                        interceptor_pkg.update_env(self.env)
                        # Call modify_env to update environment
                        interceptor_pkg.modify_env()
                        # Update our environment with changes from interceptor
                        self.env.update(interceptor_pkg.env)
                        # Also update our mod_env with interceptor's mod_env changes (for LD_PRELOAD, etc.)
                        if hasattr(self, 'mod_env') and self.mod_env:
                            self.mod_env.update(interceptor_pkg.mod_env)

    def update_config(self, kwargs, rebuild=False):
        """
        The kwargs to pack with default values

        :param kwargs: the key-word arguments to fill default values for
        :param rebuild: whether to reinitialize self.config
        from self.conifgure_menu
        :return:
        """
        Mkdir(self.private_dir,
              PsshExecInfo(hostfile=self.jarvis.hostfile))
        menu = self.configure_menu()
        menu_keys = {m['name']: True for m in menu}
        args = []
        # Convert kwargs into a list of CLI strings
        for key, val in kwargs.items():
            if val is not None:
                args.append(f'{key}={val}')
            else:
                args.append(f'{key}=')
        parser = PkgArgParse(args=args, menu=menu)
        if rebuild:
            # This will overwrite the entire configuration
            # Any parameters unspecified in the input kwargs dict
            # will be set to their default value
            self.config.update(parser.kwargs)
        else:
            # This will update the config with only the
            # parameters specified in the input kwargs dict.
            self.config.update(parser.real_kwargs)
            # If a pipeline existed before an update was made to this
            # pkg changing the parameter sets, this will ensure
            # that the config is updated with the new parameters.
            for key in parser.kwargs.keys():
                if key not in self.config:
                    self.config[key] = parser.kwargs[key]
        # This will ensure the kwargs dict contains all
        # CLI-configurable values for this pkg. The config
        # contains many parameters that may be set internally
        # by the application.
        for key, val in self.config.items():
            if key not in menu_keys:
                continue
            kwargs[key] = val

    @staticmethod
    def copy_template_file(src, dst, replacements=None):
        """
        Copy and configure an application template file
        Template files makr constants using the notation
        ##CONST_NAME##

        :param src: Path to the template
        :param dst: Destination of the template
        :param replacements: A list of 2-tuples or dict. First entry is the name
        of the constant to replace, right is the value to replace it with.
        :return: None
        """
        with open(src, 'r', encoding='utf-8') as fp:
            text = fp.read()
        if replacements is not None:
            if isinstance(replacements, list):
                for const_name, replace in replacements:
                    text = text.replace(f'##{const_name}##', str(replace))
            elif isinstance(replacements, dict):
                for const_name, replace in replacements.items():
                    text = text.replace(f'##{const_name}##', str(replace))
        with open(dst, 'w', encoding='utf-8') as fp:
            fp.write(text)


class Interceptor(SimplePkg):
    """
    An interceptor is a library which routes function calls to a custom
    function. This typically requires modifications to various environment
    variables, including LD_PRELOAD.
    """

    @abstractmethod
    def modify_env(self):
        """
        Modify the jarvis environment.

        :return: None
        """
        pass


class Service(SimplePkg):
    """
    A long-running service.
    """
    @abstractmethod
    def start(self):
        """
        Launch an application. E.g., OrangeFS will launch the servers, clients,
        and metadata services on all necessary pkgs.

        :return: None
        """
        pass

    @abstractmethod
    def stop(self):
        """
        Stop a running application. E.g., OrangeFS will terminate the servers,
        clients, and metadata services.

        :return:
        """
        pass

    @abstractmethod
    def clean(self):
        """
        Destroy all data for an application. E.g., OrangeFS will delete all
        metadata and data directories in addition to the orangefs.xml file.

        :return: None
        """
        pass

    @abstractmethod
    def status(self):
        """
        Check whether or not an application is running. E.g., are OrangeFS
        servers running?

        :return: True or false
        """
        pass


class Application(Service):
    """
    An application is a process which will terminate on its own eventually.
    This can be a benchmark program, such as IOR, for example.
    """

    def status(self):
        return True


class Pipeline(Pkg):
    """
    A pipeline connects the different pkg types together in a chain.
    """
    def _init(self):
        pass

    def configure(self, pkg_id, **kwargs):
        """
        Configure a pkg in the pipeline

        :param pkg_id: The semantic name of the pkg to configure
        :param config: Configuration parameters
        :return:
        """
        pkg = self.get_pkg(pkg_id)
        if pkg is None:
            raise Exception(f'Could not find pkg: {pkg_id}')
        pkg.update_env(self.env)
        pkg.configure(**kwargs)

    def build_env(self, env_track_dict=None):
        """
        Build the environment variable cache for this pkg.

        :param env_track_dict: a dict of booleans. Boolean indicates whether
        to track the environment variable, which are the keys of the dict.
        :return: self
        """
        exec_info = LocalExecInfo()
        self.env = exec_info.basic_env
        self.track_env(env_track_dict)
        self.update()
        return self

    def build_static_env(self, env_name, env_track_dict=None):
        """
        Build a global environment cache that can be re-used across pipelines

        :param env_name: The name of the environment to create
        :param env_track_dict: a dict of booleans. Boolean indicates whether
        to track the environment variable, which are the keys of the dict.
        :return: self
        """
        exec_info = LocalExecInfo()
        self.env = exec_info.basic_env
        self.track_env(env_track_dict)
        static_env_path = os.path.join(self.jarvis.env_dir, f'{env_name}.yaml')
        YamlFile(static_env_path).save(self.env)
        return self

    def from_yaml(self, path, do_configure=True):
        """
        Create a pipeline from a YAML file

        :param path:
        :param do_configure: Whether to append and configure
        :return: self
        """
        config = YamlFile(path).load()
        if 'loop' in config:
            return self.from_yaml_iter_dict(config, path, do_configure)
        else:
            return self.from_yaml_dict(config, path, do_configure)

    def from_yaml_dict(self, config, path=None, do_configure=True):
        """
        Create a pipeline from a YAML dict

        :param path:
        :param do_configure: Whether to append and configure
        :return: self
        """
        pipeline_id = config['name']
        self.create(pipeline_id)
        self.reset()
        if path:
            self.config['JARVIS_YAML_PATH'] = path
        if 'env' in config:
            self.copy_static_env(config['env'])
        
        # Ensure interceptors is initialized as a dictionary
        if 'interceptors' not in self.config:
            self.config['interceptors'] = {}
        
        # Store original YAML interceptors list for processing
        yaml_interceptors = config.get('interceptors', [])
        
        # Process interceptors defined at the top level
        if yaml_interceptors:
            for interceptor_config in yaml_interceptors:
                interceptor_type = interceptor_config['pkg_type']
                interceptor_name = interceptor_config['pkg_name']
                interceptor_pkg_config = interceptor_config.copy()
                del interceptor_pkg_config['pkg_type']
                del interceptor_pkg_config['pkg_name']
                
                # Create and configure the interceptor
                interceptor_pkg = self.jarvis.construct_pkg(interceptor_type)
                if interceptor_pkg is None:
                    self.log(f'Could not find interceptor pkg: {interceptor_type}', Color.RED)
                    continue
                    
                global_id = f'{self.global_id}.{interceptor_name}'
                interceptor_pkg.create(global_id)
                if do_configure:
                    interceptor_pkg.update_env(self.env)
                    interceptor_pkg.configure(**interceptor_pkg_config)
                
                # Add interceptor to the config dictionary
                self.add_interceptor(interceptor_name, interceptor_pkg)
                
        
        # Process packages (defer configuration for packages with interceptors)
        packages_to_configure = []
        for sub_pkg in config['pkgs']:
            pkg_type = sub_pkg['pkg_type']
            pkg_name = sub_pkg['pkg_name']
            pkg_config = sub_pkg.copy()
            del pkg_config['pkg_type']
            del pkg_config['pkg_name']
            
            # Check if package has interceptors
            has_interceptors = 'interceptors' in pkg_config and pkg_config['interceptors']
            
            if has_interceptors:
                # Add package without configuring it first
                self.append(pkg_type, pkg_name, False, **pkg_config)
                # Store for later configuration
                packages_to_configure.append((self.get_pkg(pkg_name), pkg_config))
            else:
                # Configure immediately for packages without interceptors
                self.append(pkg_type, pkg_name, do_configure, **pkg_config)
        
        # Now configure packages that have interceptors
        for pkg, pkg_config in packages_to_configure:
            if do_configure:
                pkg.update_env(self.env)
                pkg.configure(**pkg_config)
                
        return self

    def from_yaml_iter_dict(self, config, path=None, do_configure=True):
        """
        Create a pipeline + iterator from a YAML file
        YAML format:
        config:
          name: pipeline_name
          pkgs:
            - pkg_type: OrangeFS
              pkg_name: orangefs
              num_servers: 2
              num_clients: 4
        vars:
            pkg_id:
              - var1: [val1, val2, val3]
              - var2: [val1, val2, val3]
              - var3: [hello]
        loop:
            - [pkg_name.var1, pkg_name.var2]
            - [pkg_name.var3]
        output: my_dir

        :param path:
        :param do_configure: Whether to append and configure
        :return: self
        """
        self.from_yaml_dict(config['config'], path, do_configure)
        self.config['iterator'] = {}
        self.config['iterator']['vars'] = config['vars']
        self.config['iterator']['loop'] = config['loop']
        self.config['iterator']['output'] = config['output']
        self.config['iterator']['repeat'] = config['repeat']
        if 'kill' in config:
            self.config['iterator']['kill'] = config['kill']
        else:
            self.config['iterator']['kill'] = False
        if 'norerun' in config:
            self.config['iterator']['norerun'] = config['norerun']
        return self

    def get_static_env_path(self, env_name):
        """
        Get the path to the static environment

        :param env_name: The name of the environment
        :return: str
        """
        return os.path.join(self.jarvis.env_dir, f'{env_name}.yaml')

    def copy_static_env(self, env_name, env_track_dict=None):
        """
        Copy a cached environment to this pipeline

        :param env_name: The name of the environment to create
        :param env_track_dict: a dict of booleans. Boolean indicates whether
        to track the environment variable, which are the keys of the dict.
        :return: self
        """
        static_env_path = self.get_static_env_path(env_name)
        self.env = YamlFile(static_env_path).load()
        self.track_env(env_track_dict)
        self.update()
        return self

    def static_env_show(self, env_name):
        """
        View the contents of the static environment

        :param env_name:  The name of the environment to show
        :return: self
        """
        static_env_path = self.get_static_env_path(env_name)
        env = YamlFile(static_env_path).load()
        print(yaml.dump(env))
        return self

    def destroy_static_env(self, env_name):
        """
        Destroy a static environment file

        :param env_name: The name of the environment to create
        :return: self
        """
        static_env_path = self.get_static_env_path(env_name)
        os.remove(static_env_path)
        return self

    def list_static_env(self):
        """
        Destroy a static environment file

        :param env_name: The name of the environment to create
        """
        envs = os.listdir(self.jarvis.env_dir)
        for env in envs:
            print(env)
        return self

    def update_yaml(self):
        """
        Reload the pipeline from the stored yaml file
        """
        if 'JARVIS_YAML_PATH' in self.config:
            self.from_yaml(self.config['JARVIS_YAML_PATH'])
        else:
            self.update()
        return self

    def update(self):
        """
        Re-run configure on all sub-pkgs.

        :return: self
        """
        for pkg in self.sub_pkgs:
            pkg.env = self.env
            pkg.configure()
        return self

    def run_iter(self, resume=False):
        """
        Run the pipeline repeatedly with new configurations
        """
        self.kill = self.config['iterator']['kill']
        if resume:
            self.log('[ITER] resume=True')
        self.iterator = PipelineIterator(self)
        conf_dict = self.iterator.begin()
        self.log(f'[ITER] Will store results in: {self.iterator.stats_path}',
                 Color.BRIGHT_BLUE)
        while conf_dict is not None:
            self.clean(with_iter_out=False)
            for i in range(self.iterator.repeat):
                cur_iter_tmp = os.path.join(
                    self.iterator.iter_out,
                    f'{self.iterator.iter_count}-{i}')
                self.set_config_env_vars(cur_iter_tmp)
                self.log(f'[ITER] Iteration'
                         f'[(param) {self.iterator.iter_count + 1}/ \
                         {self.iterator.max_iter_count}]'
                         f'[(rep) {i + 1}/{self.iterator.repeat}]: '
                         f'{self.iterator.linear_conf_dict}', Color.BRIGHT_BLUE)
                self.iterator.config_pkgs(conf_dict)
                self.run(kill=self.kill)
                self.iterator.save_run(conf_dict)
                self.clean(with_iter_out=False)
            conf_dict = self.iterator.next()
        self.log('[ITER] Beginning analysis', Color.BRIGHT_BLUE)
        self.iterator.analysis()
        self.log('[ITER] Finished analysis', Color.BRIGHT_BLUE)
        self.log(f'[ITER] Stored results in: {self.iterator.stats_path}',
                 Color.BRIGHT_BLUE)

    def run(self, kill=False):
        """
        Start and stop the pipeline

        :param kill: Whether to kill the pipeline
        :return: None
        """
        self.start()
        if kill:
            self.kill()
        else:
            self.stop()

    def start(self):
        """
        Start the pipeline.

        NOTE: Start CAN hang for pipelines which spawn
        daemonized processes. This is because input/output is
        too useful to ignore. Python will attempt to close all
        file descriptors when the process exits, so the file descriptor
        used for piping output will be open for as long as the daemon.
        If using start directly, you should launch as background process.

        :return: None
        """
        self.mod_env = self.env.copy()
        for pkg in self.sub_pkgs:
            if pkg.skip_run:
                self.log(f'[RUN] (skipping) {pkg.pkg_id}: Start',
                         color=Color.YELLOW)
            else:
                self.log(f'[RUN] {pkg.pkg_id}: Start', color=Color.GREEN)

            start = time.time()
            if isinstance(pkg, Service):
                pkg.update_env(self.env)
                pkg.start()
            if isinstance(pkg, Interceptor):
                pkg.update_env(self.env)
                pkg.modify_env()
                self.mod_env.update(self.env)
            self.exit_code += pkg.exit_code
            end = time.time()
            pkg.start_time = end - start
            self.log(f'[RUN] {pkg.pkg_id}: '
                     f'Start finished in {pkg.start_time} seconds',
                     color=Color.GREEN)

    def stop(self):
        """
        Stop the pipeline

        :return: None
        """
        for pkg in reversed(self.sub_pkgs):
            self.log(f'[RUN] {pkg.pkg_id}: Stop', color=Color.GREEN)
            start = time.time()
            if isinstance(pkg, Service):
                pkg.update_env(self.env)
                pkg.stop()
            end = time.time()
            pkg.stop_time = end - start
            self.log(f'[RUN] {pkg.pkg_id}: '
                     f'Stop finished in {pkg.stop_time} seconds',
                     color=Color.GREEN)

    def kill(self):
        """
        Stop the pipeline

        :return: None
        """
        for pkg in reversed(self.sub_pkgs):
            self.log(f'[RUN] {pkg.pkg_id}: Killing', color=Color.GREEN)
            if isinstance(pkg, Service):
                pkg.update_env(self.env)
                if hasattr(pkg, 'kill'):
                    pkg.kill()
                else:
                    pkg.stop()
            self.log(f'[RUN] {pkg.pkg_id}: Finished killing', color=Color.GREEN)

    def clean(self, with_iter_out=True):
        """
        Clean the pipeline

        with_iter_out: Clean the iteration output
        :return: None
        """
        for pkg in reversed(self.sub_pkgs):
            if pkg.skip_run:
                self.log(f'[RUN] (skipping) {pkg.pkg_id}: Cleaning',
                         color=Color.YELLOW)
            else:
                self.log(f'[RUN] {pkg.pkg_id}: Cleaning', color=Color.GREEN)
            if isinstance(pkg, Service):
                pkg.update_env(self.env)
                pkg.clean()
            self.log(f'[RUN] {pkg.pkg_id}: Finished cleaning',
                     color=Color.GREEN)
        if with_iter_out and 'iterator' in self.config:
            self.iterator = PipelineIterator(self)
            Rm(self.iterator.iter_out)

    def status(self):
        """
        Get the status of the pipeline

        :return: None
        """
        statuses = []
        for pkg in reversed(self.sub_pkgs):
            self.log(f'[RUN] {pkg.pkg_id}: Getting status', color=Color.GREEN)
            status = None
            if isinstance(pkg, Service):
                pkg.update_env(self.env)
                status = pkg.status()
                statuses.append(status)
            self.log(f'[RUN] {pkg.pkg_id}: Status was {status}',
                     color=Color.GREEN)
        return math.prod(statuses)


class PipelineIndex:
    """
    Manage pipeline indexes for Jarvis
    """
    def __init__(self, index_query):
        self.jarvis = JarvisManager.get_instance()
        self.inex_query = index_query
        self.index_path = self.to_path(index_query)

    def to_path(self, index_query):
        """
        Converts an index query to pipeline index
        """
        split_query = index_query.split('.')
        repo_name = split_query[0]
        repo = self.jarvis.get_repo(repo_name)
        if repo is None:
            print(f'Could not find repo {repo_name}')
            return
        repo_path = repo['path']
        root_index_path = os.path.join(repo_path, 'pipelines')
        base_index_path = os.path.join(root_index_path, *split_query[1:])
        if not os.path.exists(root_index_path):
            print(f'repo {repo_name} has no pipeline indexes')
            return
        index_path = self._find_ext(base_index_path)
        if not os.path.exists(index_path):
            print(f'Could not find index {index_query} ({index_path})')
            return
        return index_path

    def _find_ext(self, base_path):
        for ext in ['', '.yaml', '.yml']:
            path = f'{base_path}{ext}'
            if os.path.exists(path):
                return path
        return None

    def show(self):
        """
        Print all pipeline indexes

        :return: None
        """
        if self.index_path is None:
            return self
        yamls = []
        dirs = []
        for pipeline in os.listdir(self.index_path):
            if pipeline.endswith('.yaml'):
                yamls.append(pipeline.replace('.yaml', ''))
            elif os.path.isdir(os.path.join(self.index_path, pipeline)):
                dirs.append(pipeline)

        print('SCRIPTS:')
        for script in yamls:
            print(f'  |- {script}')

        print('SUB INDEXES:')
        for subrepo in dirs:
            print(f'  |- {subrepo}')
        return self

    def copy(self, output_path):
        if self.index_path is None:
            return self
        if output_path is None:
            output_path = os.getcwd()
        shutil.copy2(self.index_path, output_path)
        return self

    def load_script(self):
        if self.index_path is None:
            return self
        pipeline = Pipeline().from_yaml(self.index_path).save()
        # try:
        #     pipeline = Pipeline().from_yaml(self.index_path).save()
        # except:
        #     print(f'Could not load pipeline {self.index_path}')
        #     return self
        self.jarvis.cd(pipeline.global_id)
        return self

    def save(self):
        self.jarvis.save()
        return self

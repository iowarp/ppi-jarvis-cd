
# Jarvis-CD

Jarvis-CD is a unified platform for deploying various applications, including storage systems and benchmarks. Many applications have complex configuration spaces and are difficult to deploy across different machines.

We provide a builtin repo which contains various applications to deploy. We refer to applications as "jarivs pkgs" which can be connected to form "deployment pipelines".

Use the argparse class to build the arguments for jarvis. Create a binary called jarvis.

Implement in jarvis_cd.core

## Main Utility Files
1. The jarvis configuration ~/.ppi-jarvis/jarvis_config.yaml
2. The repos configuration ~/.ppi-jarvis/repos.yaml
3. The resource graph ~/.ppi-jarvis/resource_graph.yaml

## Bootstrapping Jarvis

```
jarvis init [CONFIG_DIR] [PRIVATE_DIR] [SHARED_DIR]
```

* CONFIG_DIR: A directory where jarvis metadata for pkgs and pipelines are stored. This directory can be anywhere that the current user can access.
* PRIVATE_DIR: A directory which is common across all machines, but stores data locally to the machine. Some jarvis pkgs require certain data to be stored per-machine. OrangeFS is an example.
* SHARED_DIR: A directory which is common across all machines, where each machine has the same view of data in the directory.

## Creating a pipeline

```
jarvis ppl create hermes
jarvis ppl append repo.ior
jarvis ppl append ior ior2 #  Assuming repo is the top of repos.yaml, should be the same as prior command
jarvis pkg conf hermes.ior nprocs=256
```

Pipeline should have two packages: ior, ior2. 

## Jarvis Repo structure

Jarvis repos contain a set of packages. Custom repos have the following structure:

```
my_org_name
└── my_org_name
    └── orangefs
        └── package.py
```

## Register a custom repo

You can then register the repo as follows:

```bash
jarvis repo add /path/to/my_org_name
```

Whenever a new repo is added, it will be the first place
jarvis searches for pkgs.

## Creating pkgs from a template

You can then add pkgs to the repo as follows:

```bash
jarvis repo create [name] [pkg_class]
```

pkg_class can be one of:

- service
- app
- interceptor

For example:

```bash
jarvis repo create hermes service
```

The repo will then look as follows:

```
my_org_name
└── my_org_name
    ├── hermes
    │   └── package.py
    └── orangefs
        └── package.py
```

## The `Pkg` Base Class

This section will go over the variables and methods common across all Pkg types.
These variables will be initialized automatically.

```python
class Pkg:
  def __init__(self):
    self.pkg_dir = '...'
    self.shared_dir = '...'
    self.private_dir = '...'
    self.env = {}
    self.mod_env = {}
    self.config = {}
    self.global_id = '...'
    self.pkg_id = '...'
```

### `pkg_id` and `global_id`

The Global ID (global_id) is the globally unique ID of the a package in all of
jarvis. It is a dot-separated string. Typically, the format is:

```
{pipeline_id}.{pkg_id}
```

The Package ID (pkg_id) is the unique ID of the package relative to a pipeline.
This is a simple string (no dots).

For example, from section 5.1, we appended 3 packages: hermes, hermes_mpiio, and
gray_scott. hermes, hermes_mpiio, and gray_scott are also the pkg_ids. The
global_ids would be:

```
test.hermes
test.hermes_mpiio
test.gray_scott
```

Usage:

```
self.global_id
self.pkg_id
```

### `pkg_dir`

The package directory is the location of the class python file on the filesystem.
For example, when calling `jarvis repo create hermes`, the directory
created by this command will be the pkg_dir.

One use case for the pkg_dir is for creating template configuration files.
For example, OrangeFS has a complex XML configuration which would be a pain
to repeat in Python. One could include an OrangeFS XML config in their
package directory and commit as part of their Jarvis repo.

Usage:

```
self.pkg_dir
```

### `shared_dir`

The shared_dir is a directory stored on a filesystem common across all nodes
in the hostfile. Each node has the same view of data in the shared_dir. The
shared_dir contains data for the specific pkg to avoid conflicts in
a pipeline with multiple pkgs.

For example, when deploying Hermes, we assume that each node has the Hermes
configuration file. Each node is expected to have the same configuration file.
We store the Hermes config in the shared_dir.

Usage:

```
self.shared_dir
```

### `private_dir`

This is a directory which is common across all nodes, but nodes do not
have the same view of data.

For example, when deploying OrangeFS, it is required that each node has a file
called pvfs2tab. It essentially stores the protocol + address that OrangeFS
uses for networking. However, the content of this file is different for
each node. Storing it in the shared_dir would be incorrect. This is why we
need the private_dir.

Usage:

```
self.private_dir
```

### `env`

Jarvis pipelines store the current environment in a YAML file, which represents
a python dictionary. The key is the environment variable name (string) and the
value is the intended meaning of the variable. There is a single environment
used for the entire pipeline. Each pipeline stores its own environment to avoid
conflict.

Usage:

```
self.env['VAR_NAME']
```

Environments can be modified using various helper functions:

```
self.track_env(env_track_dict)
self.prepend_env(env_name, val)
self.setenv(env_name, val)
```

Viewing the env YAML file for the current pipeline from the CLI

```
cat `jarvis path`/env.yaml
```

### `mod_env`
a python dictionary. Essentially a copy of `env`. However, `mod_env` also stores the LD_PRELOAD environment variable for interception. This can cause conflict if used irresponsibly. Not every program should be intercepted.

For example, we use this for Hermes to intercept POSIX I/O. However, POSIX is widely-used for I/O so we like to be very specific when it is used.

`mod_env` can be modified using the same functions as `env`.

```
self.track_env(env_track_dict)
self.prepend_env(env_name, val)
self.setenv(env_name, val)
```

### `config`

The Jarvis configuration is stored in `{pkg_dir}/{pkg_id}.yaml`.
Unlike the environment dict, this stores variables that are specific to
the package. They are not global to the pipeline.

For example, OrangeFS and Hermes need to know the desired port number and
RPC protocol. This information is specific to the program, not the entire
pipeline.

Usage:

```
self.config['VAR_NAME']
```

### `jarvis`

The Jarvis CD configuration manager stores various properties global to
all of Jarvis. The most important information is the hostfile and resource_graph,
discussed in the next sections.

Usage:

```
self.jarvis
```

### `hostfile`

The hostfile contains the set of all hosts that Jarvis has access to.
The hostfile format is documented [here](https://github.com/scs-lab/jarvis-util/wiki/4.-Hostfile).

Usage:

```
self.jarvis.hostfile
```

### `resource_graph`

The resource graph can be queried to get storage and networking information
for storing large volumes of data.

```
self.jarvis.resource_graph
```

## Building a Service or Application

Services and Applications implement the same interface, but are logically
slightly different. A service is long-running and would typically require
the users to manually stop it. Applications stop automatically when it
finishes doing what it's doing. Jarvis can deploy services alongside
applications to avoid the manual stop when benchmarking.

### `_init`

The Jarvis constructor (`_init`) is used to initialize global variables.
Don't assume that self.config is initialized.
This is to provide an overview of the parameters of this class.
Default values should almost always be None.

```python
def _init(self):
  self.gray_scott_path = None
```

### `_configure_menu`

The function defines the set of command line options that the user can set.
An example configure menu is below:

```python
def _configure_menu(self):
    """
    Create a CLI menu for the configurator method.
    For thorough documentation of these parameters, view:
    https://github.com/scs-lab/jarvis-util/wiki/3.-Argument-Parsing

    :return: List(dict)
    """
    return [
        {
            'name': 'port',
            'msg': 'The port to listen for data on',
            'type': int,
            'default': 8080
        }
    ]
```

This function is called whenever configuring a package. For example,

```bash
jarvis pkg configure hermes --sleep=10 --port=25
```

This will configure hermes to sleep for 10 seconds after launching to give enough
time to fully start Hermes. Sleep is apart of all configure menus by default.

The format of the output dict is documented in more detail
[here](https://github.com/scs-lab/jarvis-util/wiki/3.-Argument-Parsing).

### `configure`

It takes as input a
dictionary. The keys of this dict are determined from \_configure_menu function
output. It is responsible for updating the self.config variable appropriately
and generating the application-specific configuration files.

Below is an example for Hermes. This example takes as input the port option,
modifies the hermes_server dict, and then stores the dict in a YAML file
in the shared directory.

```python
def configure(self, **kwargs):
    """
    Converts the Jarvis configuration to application-specific configuration.
    E.g., OrangeFS produces an orangefs.xml file.

    :param config: The human-readable jarvis YAML configuration for the
    application.
    :return: None
    """
    self.update_config(kwargs, rebuild=False)
    hermes_server_conf = {
      'port': self.config['port']
    }
    YamlFile(f'{self.shared_dir}/hermes_server_yaml').save(hermes_server_conf)
```

This function is called whenever configuring a packge. Specifically, this is
called immediately after \_configure_menu. For example,

```
jarvis pkg configure hermes --sleep=10 --port=25
```

will make the kwargs dict be:

```python
{
  'sleep': 10,
  'port': 25
}
```

### `start`

The start function is called during `jarvis ppl run` and `jarvis ppl start`.
This function should execute the program itself.

Below is an example for Hermes:

```python
def start(self):
    """
    Launch an application. E.g., OrangeFS will launch the servers, clients,
    and metadata services on all necessary pkgs.

    :return: None
    """
    self.daemon_pkg = Exec('hermes_daemon',
                            PsshExecInfo(hostfile=self.jarvis.hostfile,
                                         env=self.env,
                                         exec_async=True))
    time.sleep(self.config['sleep'])
    print('Done sleeping')
```

### `stop`

The stop function is called during `jarvis ppl run` and `jarvis ppl stop`.
This function should terminate the program.

Below is an example for Hermes:

```python
def stop(self):
    """
    Stop a running application. E.g., OrangeFS will terminate the servers,
    clients, and metadata services.

    :return: None
    """
    Exec('finalize_hermes',
         PsshExecInfo(hostfile=self.jarvis.hostfile,
                      env=self.env))
    if self.daemon_pkg is not None:
        self.daemon_pkg.wait()
    Kill('hermes_daemon',
         PsshExecInfo(hostfile=self.jarvis.hostfile,
                      env=self.env))
```

This is not typically implemented for Applications, but it is for Services.

### `kill`
This function is called during `jarvis ppl kill`. It should forcibly terminate a program, typically using Kill.

Below is an example for Hermes
```python
def kill(self):
    """
    Forcibly a running application. E.g., OrangeFS will terminate the
    servers, clients, and metadata services.

    :return: None
    """
    Kill('hermes_daemon',
         PsshExecInfo(hostfile=self.jarvis.hostfile,
                      env=self.env))
```

### `clean`

The `clean` function is called during `jarvis ppl clean`.
It clears all intermediate data produced by a pipeline.

Below is the prototype

```python
def clean(self):
    """
    Destroy all data for an application. E.g., OrangeFS will delete all
    metadata and data directories in addition to the orangefs.xml file.

    :return: None
    """
    pass
```

### `status`

The `status` function is called during `jarvis ppl status`
It determines whether or not a service is running. This is not typically
implemented for Applications, but it is for Services.

## Building an Interceptor

Interceptors are used to modify environment variables to route system and library
calls to new functions.

Interceptors have a slightly different interface -- they only have:
`_init`, `_configure_menu`, `configure`, and `modify_env`. The only new function
here is modify_env. The others were defined in the previous section and behave
the exact same way.

### `configure`

Configuring an interceptor tends to be a little different. The interceptors
are not typically responsible for generating configuration files like the
applications and services do. These typically are responsible solely for
modifying the environment.

Below, we show an example of configure for the Hermes MPI I/O interceptor:

```python
def configure(self, **kwargs):
    """
    Converts the Jarvis configuration to application-specific configuration.
    E.g., OrangeFS produces an orangefs.xml file.

    :param kwargs: Configuration parameters for this pkg.
    :return: None
    """
    self.update_config(kwargs, rebuild=False)
    self.config['HERMES_MPIIO'] = self.find_library('hermes_mpiio')
    if self.config['HERMES_MPIIO'] is None:
        raise Exception('Could not find hermes_mpiio')
    print(f'Found libhermes_mpiio.so at {self.config["HERMES_MPIIO"]}')
```

Here we use self.find_library() to check if we can find the shared library
hermes_mpiio in the system paths. This function introspects LD_LIBRARY_PATH
and determines if hermes_mpiio is in the path. It saves the path in the pkg
configuration (self.config).

### `modify_env`

Below is an example of the MPI I/O interceptor for Hermes:

```python
def modify_env(self):
    """
    Modify the jarvis environment.

    :return: None
    """
    self.prepend_env('LD_PRELOAD', self.config['HERMES_MPIIO'])
```

### Example Package: IOR

```python
"""
This module provides classes and methods to launch the Ior application.
Ior is a benchmark tool for measuring the performance of I/O systems.
It is a simple tool that can be used to measure the performance of a file system.
It is mainly targeted for HPC systems and parallel I/O.
"""
from jarvis_cd.core.pkg import Application
from jarvis_util import *
import os


class Ior(Application):
    """
    This class provides methods to launch the Ior application.
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
        ]

    def _configure(self, **kwargs):
        """
        Converts the Jarvis configuration to application-specific configuration.
        E.g., OrangeFS produces an orangefs.xml file.

        :param kwargs: Configuration parameters for this pkg.
        :return: None
        """
        self.config['api'] = self.config['api'].upper()

    def start(self):
        """
        Launch an application. E.g., OrangeFS will launch the servers, clients,
        and metadata services on all necessary pkgs.

        :return: None
        """
        cmd = [
            'ior',
            '-k',
            f'-b {self.config["block"]}',
            f'-t {self.config["xfer"]}',
            f'-a {self.config["api"]}',
            f'-o {self.config["out"]}',
        ]
        out = os.path.expandvars(self.config['out'])
        if self.config['write']:
            cmd.append('-w')
        if self.config['read']:
            cmd.append('-r')
        if self.config['fpp']:
            cmd.append('-F')
        if self.config['reps'] > 1:
            cmd.append(f'-i {self.config["reps"]}')
        if '.' in os.path.basename(out):
            os.makedirs(str(pathlib.Path(out).parent),
                        exist_ok=True)
        else:
            os.makedirs(out, exist_ok=True)
        # pipe_stdout=self.config['log']
        Exec('which mpiexec',
             LocalExecInfo(env=self.mod_env))
        Exec(' '.join(cmd),
             MpiExecInfo(env=self.mod_env,
                         hostfile=self.jarvis.hostfile,
                         nprocs=self.config['nprocs'],
                         ppn=self.config['ppn'],
                         do_dbg=self.config['do_dbg'],
                         dbg_port=self.config['dbg_port']))

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
        Rm(self.config['out'] + '*',
           PsshExecInfo(env=self.env,
                        hostfile=self.jarvis.hostfile))

    def _get_stat(self, stat_dict):
        """
        Get statistics from the application.

        :param stat_dict: A dictionary of statistics.
        :return: None
        """
        stat_dict[f'{self.pkg_id}.runtime'] = self.start_time
```




# Pipeline Scripts

Pipeline scripts are useful for storing cross-platform unit tests.
They store all of the information needed to create and execute
a pipeline.

## Running a pipline script

Pipeline scripts are YAML files and can be executed as follows:
```bash
jarvis ppl load yaml /path/to/my_pipeline.yaml
jarvis ppl run
```

Alternatively, if you want to load + run the script:
```bash
jarvis ppl run yaml /path/to/my_pipeline.yaml
```

## Updating a pipeline

To load changes made to a pipeline script, you can run:
```bash
jarvis ppl update yaml
```

The pipeline will store the path so you don't have to repeat.

```python
name: chimaera_unit_ipc
env: chimaera
pkgs:
  - pkg_type: chimaera_run
    pkg_name: chimaera_run
    sleep: 10
    do_dbg: true
    dbg_port: 4000
  - pkg_type: chimaera_unit_tests
    pkg_name: chimaera_unit_tests
    TEST_CASE: TestBdevIo
    do_dbg: true
    dbg_port: 4001
    interceptors: hermes_api
interceptors:
  - pkg_type: hermes_api
    pkg_name: hermes_api
```

## Class loader

This should be used to dynamically load packages.

```python
def load_class(import_str, path, class_name):
    """
    Loads a class from a python file.

    :param import_str: A python import string. E.g., for "myrepo.dir1.pkg"
    :param path: The absolute path to the directory which contains the
    beginning of the import statement. Let's say you have a git repo located
    at "/home/hello/myrepo". The git repo has a subdirectory called "myrepo",
    so "/home/hello/myrepo/myrepo". In this case, path would be
    "/home/hello/myrepo". The import string "myrepo.dir1.pkg" will find
    the "myrepo" part of the import string at "/home/hello/myrepo/myrepo".
    :param class_name: The name of the class in the file
    :return: The class data type
    """
    fullpath = os.path.join(path, import_str.replace('.', '/') + '.py')
    if not os.path.exists(fullpath):
        return None
    sys.path.insert(0, path)
    module = __import__(import_str, fromlist=[class_name])
    cls = getattr(module, class_name)
    sys.path.pop(0)
    return cls

```


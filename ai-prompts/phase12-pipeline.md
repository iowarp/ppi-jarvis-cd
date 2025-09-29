mod_env should be an exact replica of env, except with LD_PRELOAD. LD_PRELOAD should
not be in env at any point. 

I want you to consolidate. Merge PipelineManager and PackageManager with Pkg and Pipeline. Pipeline is a new class. at a high level, the changes that should be made are as follows. Ideally, the pipeline and pkg classes will be in core instead of basic. I would like the basic directory removed. Udpate the CLI code to use these instead.

Pipeline:
1. __init__: Set all parameters and expected variables of the pipeline to reasonable values to avoid requiring hasattr everywhere. It is required for user to externally call load or create later. Users expected to know if the pipeline exists or not. Use the Jarvis singleton to get paths like conf_dir, shared_dir, and priv_dir.
1. create: create a pipeline. pipelines have environments and a config (a set of packages)
1. load: load the pipeline. Loads each package of the pipeline
1. save: call save for each package in the pipeline and then save my configuration
1. destroy: delete the pipeline directory
1. start: iterate over each package forward and call start()
1. stop: iterate over each package backward and call stop()
1. kill: like stop, but with kill
1. status: iterate over each package forward and call status()
1. run. start then stop.
1. append: append package to pipeline and call its create function
1. rm: remove a package from the pipeline and call its destroy function

Pkg:
1. __init__: Set all parameters and expected variables of the package to reasonable values to avoid requiring hasattr everywhere. It is required for user to externally call load or create later.  Use the Jarvis singleton to get paths like conf_dir, shared_dir, and priv_dir.
1. create: a method to create a package. Packages should be created as subdirectories in their parent pipeline. Take the parent pipeline as input in addition to other package parameters. 
1. load: load package configuration and environment variables
1. save: save package configuration and environment variables
1. destroy: delete the package directories shared_dir, conf_dir, and priv_dir, but NOT pkg_dir.
1. _configure_menu: abstract
1. configure_menu(): calls _configure_menu, but updates the arg dict with common arguments.
1. configure: abstract
1. start: abstract
1. stop: abstract
1. kill: abstract
1. status: abstract


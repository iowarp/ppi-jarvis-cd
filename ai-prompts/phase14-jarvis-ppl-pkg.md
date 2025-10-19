@CLAUDE.md Use the python code updater agent.

The way the pipelines and pkgs are stored is incorrect. Currently, pipelines, packages, and the environment are represented as a single yaml file stored in the pipeline's config_dir.
This is not correct. It needs more separation.

For pipelines, we need the following:
1. A pipeline configuration yaml that stores the set of packages and interceptors. This represents ordering and existence. This does not include package parameters or environments. It should be the same exact format as the pipeline script, with the pkgs and interceptors sections. Hopefully this will allow us to reduce code.
2. A pipeline environment yaml. Stores environment variables. When loading a pipeline, this environment will be passed to each subsequent package.

We can remove the package load() and save() methods with this new idea.

Packages should always require the pipeline is input. No default value None, it is a requirement. In addition, config_dir, private_dir, and shared_dir should be initialized during __init__. These are fixed paths based on the pipeline directories. 

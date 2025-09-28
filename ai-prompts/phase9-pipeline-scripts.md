# Pipeline Scripts

Use the python-code-updater agent to change the structure of pipleine scripts. 

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

## Format

The format should look like this:
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

In the Pkg class, there should be a new function called add_interceptor. This should modify a new self.config key called 'interceptors'. The interceptors key will be similar to the sub_pkgs key. The set of interceptors should be stored in a dictionary. This dictionary should be a mapping of pkg_name to a constructed package.

In SimplePackage, add a new config parameter called "interceptors", which is a list of strings. The list parameters look like this:
```
 self.add_args([
            {
                'name': 'hosts',
                'msg': 'A list of hosts and threads pr',
                'type': list,
                'args': [
                    {
                        'name': 'host',
                        'msg': 'A string representing a host',
                        'type': str,
                    }
                ]
            }
        ])
```

When loading a SimplePackage, iterate over the set of strings there and check self.ppl for the interceptors. Call interceptor.modify_env() to update our environment. Remove the ability to pass mod_env to update_env function. Make it so mod_env is a copy (not pointer) to env. This way each package gets its own isolated module environment.
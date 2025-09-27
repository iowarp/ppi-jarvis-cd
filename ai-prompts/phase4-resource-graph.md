
## Resource Graph

For each available storage device, identify:
1. mount_point
2. available_size
3. 

## Jarvis Environment

``jarvis env build``

## Jarvis Package

A jarvis package has the following components:
```
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

## Pipeline Script

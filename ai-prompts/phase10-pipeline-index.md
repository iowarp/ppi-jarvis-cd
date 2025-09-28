# Pipeline Indexes

Pipeline indexes are folders containing pipeline scripts.
They can be used to disseminate working examples of your code.
For example, pipelines scripts used for unit tests would be good to have
in a pipeline index.

## Adding a Pipeline Index

Pipeline indexes are stored within repos as a subdirectory named
``pipelines``. It is required to be named ``pipelines``.

Below is an example structure of a jarvis repo containing a pipeline index.
```bash
jarvis_chimaera # Repo
├── jarvis_chimaera  # Jarvis Packages
│   ├── chimaera_bw_bench
│   ├── chimaera_docker
│   ├── chimaera_latency_bench
│   ├── chimaera_run
│   ├── chimaera_unit_tests
│   └── chimaera_zlib_bench
└── pipelines  # Pipeline Index
    ├── bench_bw_ipc.yaml
    ├── bench_latency_ipc.yaml
    ├── test_bdev_io.yaml
    ├── test_bdev_ram.yaml
    ├── test_bulk_ipc.yaml
    ├── test_bulk_read_ipc.yaml
    ├── test_bulk_write_ipc.yaml
    ├── test_compress.yaml
    ├── test_ipc_rocm.yaml
    ├── test_ipc.yaml
    ├── test_python.yaml
    ├── test_serialize.yaml
    └── test_upgrade.yaml
```

Below is another example with an index containing subdirectories:
```bash
jarvis_hermes  # Repo
├── jarvis_hermes  # Jarvis Packages
│   ├── hermes_api
│   │   ├── pkg.py
│   │   └── README.md
│   ├── hermes_api_bench
│   │   ├── pkg.py
│   │   └── README.md
└── pipelines  # Pipeline Index
    ├── hermes
    │   └── test_hermes.yaml
    ├── mpiio
    │   ├── test_hermes_mpiio_basic_async.yaml
    │   ├── test_hermes_mpiio_basic_sync.yaml
    │   └── test_mpiio_basic.yaml
    ├── nvidia_gds
    │   ├── test_hermes_nvidia_gds.yaml
    │   └── test_nvidia_gds_basic.yaml
    ├── posix
    │   ├── test_hermes_posix_basic_large.yaml
    │   ├── test_hermes_posix_basic_mpi_large.yaml
    │   ├── test_hermes_posix_basic_mpi_small.yaml
    ├── stdio
    │   ├── test_hermes_stdio_adapter_bypass.yaml
    │   ├── test_hermes_stdio_adapter_default.yaml
    │   ├── test_hermes_stdio_adapter_scratch.yaml
    │   ├── test_hermes_stdio_basic_large.yaml
    ├── test_borg.yaml
    ├── test_ior.yaml
    └── vfd
        ├── test_hermes_vfd_basic.yaml
        ├── test_hermes_vfd_python.yaml
        ├── test_hermes_vfd_scratch.yaml
        └── test_vfd_python.yaml
```

## List indexes

Since pipeline indexes are stored in repos, just list
the repos
```bash
jarvis repo list
```

## Index Queries

In the commands below, many commands have the parameter ``[index_query]``.
An index query is a dotted string in the following format:
```
[repo_name].[subdir1]...[subdirN].[script]
```

For example:
```
jarvis_chimaera.bench_bw_ipc
jarvis_hermes.hermes.test_hermes
``` 

NOTE: index queries do not include file extensions.

## Use a script from an index
To call a pipeline script stored in an index directly, you
can do:

```bash
jarvis ppl index load [index_query]
```

For example:
```bash
jarvis ppl index load jarvis_chimaera.bench_bw_ipc
jarvis ppl index load jarvis_hermes.hermes.test_hermes
```

## Copy a script from an index

You can copy a pipeline script from an index to your current
directory or some other directory. You can then edit the
parameters to the script and the call ``jarvis ppl load yaml``
on your modified script.

To copy the script from an index:
```bash
jarvis ppl index copy [index_query] [output (optional)]
```

Parameters:
* index_query: a dotted string indicating the script in the index to copy
* output: a directory of file to copy the script to. If output is not provided,
it will copy to the current working directory.

For example:
```bash
jarvis ppl index copy jarvis_chimaera.bench_bw_ipc
jarvis ppl index copy jarvis_hermes.hermes.test_hermes
```

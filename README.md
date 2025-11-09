# Jarvis-CD

Jarvis-CD is a unified platform for deploying various applications, including storage systems and benchmarks. Many applications have complex configuration spaces and are difficult to deploy across different machines.

## Installation

```bash
cd /path/to/jarvis-cd
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
```

## Configuration (Build your Jarvis setup)

```bash
jarvis init [CONFIG_DIR] [PRIVATE_DIR] [SHARED_DIR]
```
- CONFIG_DIR: Stores Jarvis metadata for pkgs/pipelines (any path you can access)
- PRIVATE_DIR: Per-machine local data (e.g., OrangeFS state)
- SHARED_DIR: Shared across machines with the same view of data

On a personal machine, these can point to the same directory.

## Hostfile (set target nodes)

The hostfile lists nodes for multi-node pipelines (MPI-style format):

Example:
```text
host-01
host-[02-05]
```

Set the active hostfile:
```bash
jarvis hostfile set /path/to/hostfile
```

After changing the hostfile, update the active pipeline:
```bash
jarvis ppl update
```

## Resource Graph (discover storage)

```bash
jarvis rg build
```

## License

BSD-3-Clause License - see [LICENSE](LICENSE) file for details.

**Copyright (c) 2024, Gnosis Research Center, Illinois Institute of Technology**

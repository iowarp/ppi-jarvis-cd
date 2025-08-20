# Jarvis-CD

Jarvis-CD is a unified platform for deploying various applications, including storage systems and benchmarks. Many applications have complex configuration spaces and are difficult to deploy across different machines.

We provide a builtin repo which contains various applications to deploy. We refer to applications as "jarivs pkgs" which can be connected to form "deployment pipelines".

- Full docs: https://grc.iit.edu/docs/jarvis/jarvis-cd/index
- GitHub: https://github.com/iowarp/ppi-jarvis-cd

## Installation

You can install Jarvis-CD via Spack (recommended) or Pip. If you already installed IOWarp, Jarvis-CD is included as a dependency—skip to Configuration.

### Option A: Install with Spack

1) Install Spack and initialize the environment
```bash
cd ${HOME}
git clone https://github.com/spack/spack.git
cd spack
git checkout tags/v0.22.2
echo ". ${PWD}/share/spack/setup-env.sh" >> ~/.bashrc
source ~/.bashrc
```

2) Add the IOWarp Spack repo
```bash
cd ${HOME}
git clone https://github.com/iowarp/iowarp-install.git
spack repo add iowarp-install/iowarp-spack
```

3) Install Jarvis-CD and load it
```bash
spack external find python
spack install py-ppi-jarvis-cd
spack load py-ppi-jarvis-cd
```

Note: Spack packages must be loaded in each new terminal session.

### Option B: Install with Pip (developers)

Install jarvis-util first, then Jarvis-CD from source. This path is useful for local development.

1) jarvis-util
```bash
git clone https://github.com/grc-iit/jarvis-util.git
cd jarvis-util
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
```

2) Jarvis-CD
```bash
cd /path/to/jarvis-cd
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
```

3) Optional: network test utility
```bash
spack install ppi-chi-nettest
```

## Configuration (Build your Jarvis setup)

Choose one of the following to create your Jarvis configuration.

### A) Single machine (quick start)
```bash
jarvis bootstrap from local
```

### B) Use a pre-configured machine

Some machines (IIT, Sandia, Argonne, etc.) are preconfigured.

List available machines:
```bash
jarvis bootstrap list
```

Bootstrap from a known machine:
```bash
jarvis bootstrap from [machine-name]
```

Note: Don’t bootstrap from an unknown machine—it can break deployments.

### C) Create a new configuration from scratch
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

## Passwordless SSH (multi-node convenience)

For clouds/bare-metal (e.g., Chameleon, CloudLab), set up SSH keys across nodes.

1) Copy your key to a seed node (example IP):
```bash
jarvis ssh copy ~/.ssh/id_ed25519 129.127.0.124
```

2) Set your hostfile with all target nodes:
```bash
jarvis hostfile set ~/hostfile.txt
```

3) Distribute the key to all nodes:
```bash
jarvis ssh distribute ~/.ssh/id_ed25519
```

## Resource Graph (discover networks and storage)

Build once after “bootstrap from local” or “init” (skip if you bootstrapped from a known machine):
```bash
jarvis rg build
```

This snapshots network/storage topology for package configuration (e.g., Hermes). Re-run if resources change (e.g., add a drive).

Tips for hostfile before building:
1) Include at least two representative nodes for multi-node deployments so valid networks can be detected.
2) Avoid using the master/login node in the set you introspect unless representative of your deployment nodes.

## License

BSD-3-Clause License - see [LICENSE](LICENSE) file for details.

**Copyright (c) 2024, Gnosis Research Center, Illinois Institute of Technology**

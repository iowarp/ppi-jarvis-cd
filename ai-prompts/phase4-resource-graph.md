# Resource Graph

Resource graph contains primarily storage resources. It automatically collects the set of mounted storage devices, only the ones that the current user has permissions to read or write to. 

Ideally, the introspection would use a portable python library to determine the following information, but if systems-specific tools are needed that is ok too.

## Resource Collection Binary

We should have a resource graph collection binary file that executes per-machine. this will collect
the machine state per-machine

## Resource Graph Class

We should have a resource graph class that is placed in jarvis_cd.util

## Generate resource graph

```yaml
jarvis rg build
```

Using the current hostfile (set by ``jarvis hostfile set``), it will collect the set of storage devices on each node in the hostfile and then produce a view of common storages between the nodes.
They are required to have the same mount point.

You also should run a benchmark for 25 seconds on each storage device to get the initial performance profile of the storage devices. Run the profiles on separate threads. Collect 4KB randwrite bandwidht and 1MB seqwrite bandwidth.

We will need to build a new jarvis_cd.shell command to wrap around the resource_graph python script you will build in the bin directory. It should inherit from Exec. The jarvis ppl rg build should use PsshExecInfo for this execution.

## Storage configuration

Ideally, the following information would be collected:
```yaml
fs:
- avail: 500GB
  dev_type: ssd
  device: /dev/sdb1
  fs_type: xfs
  model: Samsung SSD 860
  mount: /mnt/ssd/${USER}
  parent: /dev/sdb
  shared: false  # is this a PFS or local storage? 
  needs_root: false  # can the user read /write here?
  4k_randwrite_bw: 8mbps  
  1m_seqwrite_bw: 1000mbps
```


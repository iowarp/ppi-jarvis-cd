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
  shared: false
  uuid: 45b6abb3-7786-4b68-95d0-a8fac92e0d70
  needs_root: false
  4k_randwrite_bw: 8mbps
  1m_seqwrite_bw: 1000mbps
```

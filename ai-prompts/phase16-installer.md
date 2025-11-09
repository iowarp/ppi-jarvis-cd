@CLAUDE.md 

I have done a hard reset. Currently, we are building container images during configure of each package. This is not inefficient. We should separate the building of containers from pipelines entirely. Instead, let's create a new concept called installers. Installers will allow us to build docker containers that have all the dependencies necessary to execute containerized pipelines.

## Pipeline Script Update
```
env: env_name
container_name: my_iowarp
container_engine: podman
container_base: iowarp/iowarp-build:latest
pkgs:
interceptors:
```

New parameters: container_name, container_engine, container_base.
container_name is default "", indicating the pipeline is not containerized.
container_engine is default podman.
container_base is default iowarp:iowarp-deps:latest. 
Container image files will be stored in ~/.ppi-jarvis/containers/container_name.Dockerfile
A container mainfest indicating the packages installed in the container will be stored in ~/.ppi-jarvis/containers/container_name.yaml
Create the files if they do not already exist.

## Container Manifest

This is a YAML file indicating the packages installed in the container.
Will be stored in ~/.ppi-jarvis/containers/container_name.yaml

```yaml
pkg_type: deploy_mode
```

pkg_type should be the concretized pacakge type. For example, builtin.ior points to the builtin repo's ior package.
It should not be pipeline-specific package names.

## jarvis ppl load yaml [path]

This will load a pipeline script. With these new parameters, we first must build the container image for container_name.
This is done by iterating over each pkgs and interceptors value in the pipeline, calling a new method augment_container.
This method is static and should be apart of the Package base class.
Packages can inherit this to augment the container image file with its specific installation steps.

The container manifest and image should be loaded from ~/.ppi-jarvis/container_name.yaml and ~/.ppi-jarvis/container_name.Dockerfile.
When iterating, check if a package is already apart of the built container.
If it is, then skip calling its augment_container function and go next.

## pkg base config menu

Packages have a deploy_mode parameter. 

A package should support multiple baremetal and containerized deployments. The choice of container should be made per-package.
Each package can set the deploy_mode to indicate the specific option they want to augment the dockerfile with.

I believe this is already supported in the current implementation. We also already have the RouteApp and RouteService package types,
in addition to ContainerApp and ContainerService. There should not be any changes needed here.

## pkg.augment_container()

This should return a string (in the format of a dockerfile) containing how to install the dependencies
for the particular container. This should be called right after pkg.configure() during pipeline's configure function.
It should be called only if the package has not been installed the container already. To check if it has been installed,
we must check the container manifest. This file stores a dictionary of all packages installed. If this package is in the
manifest and has the same deploy_mode, then skip. If it is in the manifest, but has a different deploy_mode, then print
an error saying this is not allowed to have different versions installed in the same container.

## jarvis container remove [container_name]
Destroy the image container_name. Remove the files associated with it in ~/.ppi-jarvis-containers

## jarvis container list
List the set of containers in ~/.ppi-jarvis/containers

## jarvis ppl conf container_name=X container_engine=Y container_base=Z

Add a new jarvis ppl conf parameter. It takes as input containerize as a bool for now.

This will put the pipeline in a "container" deployment mode, rather than the default mode.

This will indicate that each package in the pipeline should use the container deployment mode.
Every existing package in the pipeline will be reconfigured to use deploy_mode=container_engine

## jarvis ppl create [pipeline_name] [container_name (default="")]

Update jarvis ppl create to allow us to create containerized pipelines without requiring a call to jarvis ppl containerize.
The container_name and container_engine stored in the pipeline yaml file.
When packages are being configured, the configure function should check the parent pipeline for container_name and container_engine.
This will be used to set the deploy_mode

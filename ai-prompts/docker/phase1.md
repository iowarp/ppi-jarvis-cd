@CLAUDE.md 

Let's make two dockerfiles under the directory docker: 
build.Dockerfile and deploy.Dockerfile.

build and deploy should be built in the github actions. Manual only. Please edit the github actions. Add a new action called build_dockerfiles.yml

## build.Dockerfile

Pip install from workspace. Mount the parent directory as /workspace. 
Add to spack.

```Dockerfile
FROM iowarp/iowarp-deps:latest
LABEL maintainer="llogan@hawk.iit.edu"
LABEL version="0.0"
LABEL description="IOWarp ppi-jarvis-cd Docker image"

# Add ppi-jarvis-cd to Spack configuration
RUN echo "  py-ppi-jarvis-cd:" >> ~/.spack/packages.yaml && \
    echo "    externals:" >> ~/.spack/packages.yaml && \
    echo "    - spec: py-ppi-jarvis-cd" >> ~/.spack/packages.yaml && \
    echo "      prefix: /usr/local" >> ~/.spack/packages.yaml && \
    echo "    buildable: false" >> ~/.spack/packages.yaml

# Setup jarvis
RUN jarvis init
```

Also create a local.sh in docker directory to build the container locally. Should look something like this:
```bash
#!/bin/bash

# Build iowarp-runtime Docker image

# Get the project root directory (parent of docker folder)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/.." && pwd )"

echo $PROJECT_ROOT
echo $SCRIPT_DIR
# Build the Docker image
docker build  --no-cache -t iowarp/ppi-jarvis-cd-build:latest -f "${SCRIPT_DIR}/build.Dockerfile" "${PROJECT_ROOT}"
```

## deploy.Dockerfile

Essentially just does ``FROM iowarp/ppi-jarvis-cd-build:latest`` for now.

In the github action, create ``iowarp/ppi-jarvis-cd:latest``.


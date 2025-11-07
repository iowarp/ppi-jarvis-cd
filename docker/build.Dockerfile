FROM iowarp/iowarp-deps:latest
LABEL maintainer="llogan@hawk.iit.edu"
LABEL version="0.0"
LABEL description="IOWarp ppi-jarvis-cd Docker image"

# Copy the workspace
COPY . /workspace
WORKDIR /workspace

# Clean any existing build artifacts and install the package
RUN sudo rm -rf *.egg-info build dist && \
    sudo pip install --break-system-packages .

# Add ppi-jarvis-cd to Spack configuration
RUN echo "  py-ppi-jarvis-cd:" >> ~/.spack/packages.yaml && \
    echo "    externals:" >> ~/.spack/packages.yaml && \
    echo "    - spec: py-ppi-jarvis-cd" >> ~/.spack/packages.yaml && \
    echo "      prefix: /usr/local" >> ~/.spack/packages.yaml && \
    echo "    buildable: false" >> ~/.spack/packages.yaml

# Setup jarvis
RUN jarvis init

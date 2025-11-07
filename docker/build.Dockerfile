FROM iowarp/iowarp-deps:latest
LABEL maintainer="llogan@hawk.iit.edu"
LABEL version="0.0"
LABEL description="IOWarp ppi-jarvis-cd Docker image"

# Copy the workspace
COPY . /workspace
WORKDIR /workspace

# Install the package
RUN pip install -e .

# Add ppi-jarvis-cd to Spack configuration
RUN echo "  py-ppi-jarvis-cd:" >> ~/.spack/packages.yaml && \
    echo "    externals:" >> ~/.spack/packages.yaml && \
    echo "    - spec: py-ppi-jarvis-cd" >> ~/.spack/packages.yaml && \
    echo "      prefix: /usr/local" >> ~/.spack/packages.yaml && \
    echo "    buildable: false" >> ~/.spack/packages.yaml

# Setup jarvis
RUN jarvis init

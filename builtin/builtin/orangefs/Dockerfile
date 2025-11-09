FROM iowarp/iowarp-build:latest

# Set non-interactive frontend to avoid prompts
ENV DEBIAN_FRONTEND=noninteractive

# Set timezone to avoid prompt during package installation
ENV TZ=Etc/UTC

# Update package lists
RUN apt-get update && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Reset frontend
ENV DEBIAN_FRONTEND=dialog

# SCSPKG + lmod
RUN echo $'\n\
    if ! shopt -q login_shell; then\n\
    if [ -d /etc/profile.d ]; then\n\
    for i in /etc/profile.d/*.sh; do\n\
    if [ -r $i ]; then\n\
    . $i\n\
    fi\n\
    done\n\
    fi\n\
    fi\n\
    ' >> /root/.bashrc
RUN . "${SPACK_DIR}/share/spack/setup-env.sh" && \
    spack load iowarp && \
    echo "module use $(scspkg module dir)" >> /root/.bashrc && \
    scspkg init tcl

# Install OFS dependencies
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y automake bison flex \
    libdb-dev \
    libsqlite3-dev libfuse-dev fuse

# Install libfuse
RUN . "${SPACK_DIR}/share/spack/setup-env.sh" && \
    spack install libfuse@2.9

# Install OFS
RUN . "${SPACK_DIR}/share/spack/setup-env.sh" && \
    spack load iowarp libfuse && \
    scspkg create orangefs && \
    cd $(scspkg pkg src orangefs) && \
    wget https://github.com/waltligon/orangefs/releases/download/v.2.10.0/orangefs-2.10.0.tar.gz && \
    tar -xvzf orangefs-2.10.0.tar.gz && \
    cd orangefs && \
    ./prepare && \
    ./configure --prefix=$(scspkg pkg root orangefs) --enable-shared --enable-fuse && \
    make -j8 && \
    make install && \
    scspkg env prepend orangefs ORANGEFS_PATH $(scspkg pkg root orangefs)

# Install OFS with openmpi


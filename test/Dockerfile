FROM ubuntu:22.04

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    gcc \
    g++ \
    make \
    git \
    openssh-client \
    openssh-server \
    rsync \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Install MPI for MPI tests (optional)
RUN apt-get update && apt-get install -y \
    openmpi-bin \
    libopenmpi-dev \
    && rm -rf /var/lib/apt/lists/*

# Configure SSH server
RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Create test user
RUN useradd -m -s /bin/bash testuser && \
    echo "testuser:testpass" | chpasswd && \
    usermod -aG sudo testuser

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Install test dependencies
RUN pip3 install --no-cache-dir \
    pytest>=8.0.0 \
    pytest-cov>=4.0.0 \
    pytest-xdist>=3.0.0 \
    coverage>=7.0.0

# Copy the entire project
COPY . /app/

# Compile test binaries
RUN gcc /app/test/unit/shell/test_env_checker.c -o /app/test/unit/shell/test_env_checker

# Set up SSH keys for testuser (passwordless SSH to localhost)
RUN mkdir -p /home/testuser/.ssh && \
    ssh-keygen -t rsa -N "" -f /home/testuser/.ssh/id_rsa && \
    cat /home/testuser/.ssh/id_rsa.pub >> /home/testuser/.ssh/authorized_keys && \
    chmod 700 /home/testuser/.ssh && \
    chmod 600 /home/testuser/.ssh/authorized_keys && \
    chmod 600 /home/testuser/.ssh/id_rsa && \
    chown -R testuser:testuser /home/testuser/.ssh

# Configure SSH client for testuser
RUN echo "Host localhost" >> /home/testuser/.ssh/config && \
    echo "    StrictHostKeyChecking no" >> /home/testuser/.ssh/config && \
    echo "    UserKnownHostsFile=/dev/null" >> /home/testuser/.ssh/config && \
    chmod 600 /home/testuser/.ssh/config && \
    chown testuser:testuser /home/testuser/.ssh/config

# Change ownership to test user
RUN chown -R testuser:testuser /app

# Switch to test user
USER testuser

# Set Python path
ENV PYTHONPATH=/app:$PYTHONPATH

# Create entrypoint script to start SSH daemon
USER root
RUN echo '#!/bin/bash\n\
# Start SSH daemon\n\
sudo /usr/sbin/sshd\n\
# Wait for SSH to be ready\n\
sleep 2\n\
# Execute the command passed to the container\n\
exec "$@"\n\
' > /entrypoint.sh && \
    chmod +x /entrypoint.sh && \
    chown testuser:testuser /entrypoint.sh

# Allow testuser to run sshd without password
RUN echo "testuser ALL=(ALL) NOPASSWD: /usr/sbin/sshd" >> /etc/sudoers

USER testuser

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command runs all tests
CMD ["python3", "-m", "pytest", "test/unit/", "-v", "--cov=jarvis_cd", "--cov-report=term-missing", "--cov-report=html:/app/htmlcov"]

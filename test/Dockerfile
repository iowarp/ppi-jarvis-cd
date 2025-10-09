FROM ubuntu:22.04

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3-pip \
    python3-venv \
    gcc \
    g++ \
    make \
    git \
    openssh-client \
    rsync \
    && rm -rf /var/lib/apt/lists/*

# Install MPI for MPI tests (optional)
RUN apt-get update && apt-get install -y \
    openmpi-bin \
    libopenmpi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create test user
RUN useradd -m -s /bin/bash testuser

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

# Change ownership to test user
RUN chown -R testuser:testuser /app

# Switch to test user
USER testuser

# Set Python path
ENV PYTHONPATH=/app:$PYTHONPATH

# Default command runs all tests
CMD ["python3", "-m", "pytest", "test/unit/", "-v", "--cov=jarvis_cd", "--cov-report=term-missing", "--cov-report=html:/app/htmlcov"]

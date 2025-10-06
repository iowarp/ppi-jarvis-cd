#!/bin/bash
# Script to build and test the Docker test image

set -e

echo "Building Docker test image..."
docker build -f Dockerfile.test -t jarvis-cd-test:latest .

echo ""
echo "Running tests in Docker container..."
docker run --rm jarvis-cd-test:latest

echo ""
echo "Test execution complete!"

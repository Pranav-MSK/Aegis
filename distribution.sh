#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status
set -x  # Enable debugging output

pyarmor_distribution() {
    # Create as dist directory
    pyarmor gen -O dist src || { echo "PyArmor generation failed"; exit 1; }

    cp app.py dist || { echo "Failed to copy app.py"; exit 1; }
    cp -r src/assets dist/src || { echo "Failed to copy assets"; exit 1; }
    cp -r src/templates dist/src || { echo "Failed to copy templates"; exit 1; }
    cp -r src/static dist/src || { echo "Failed to copy static"; exit 1; }
    cp -r src/scripts dist/src || { echo "Failed to copy scripts"; exit 1; }
    cp .env dist || { echo "Failed to copy .env"; exit 1; }
}

pyarmor_distribution
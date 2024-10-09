#!/bin/bash

# Define directories
ROOT_DIRECTORY=$(pwd)
SOURCE_DIRECTORY="$ROOT_DIRECTORY/src"
COMPILED_CODE_DIRECTORY="$ROOT_DIRECTORY/compiled_code"
COMPILED_CODE_SOURCE_DIRECTORY="$COMPILED_CODE_DIRECTORY/src"
PROMETHEUS_OUTPUT_DIRECTORY="$COMPILED_CODE_DIRECTORY/prometheus_config"

# Create necessary directories
mkdir -p "$PROMETHEUS_OUTPUT_DIRECTORY"

# Function to find all .py files in the source directory
find_python_files() {
    python_files=()
    while IFS= read -r -d '' file; do
        python_files+=("$file")
    done < <(find "$SOURCE_DIRECTORY" -name '*.py' -print0)
    echo "${python_files[@]}"
}

# Function to compile .py files to .c files using Cython
generate_c_files() {
    echo "Generating C files from Python files..."
    local python_files
    python_files=$(find_python_files)

    for python_file in $python_files; do
        cython "$python_file" -o "${python_file%.py}.c" || {
            echo "Error: Failed to generate C file for '$python_file'"
            exit 1
        }
    done
}

# Function to compile .c files to .so files
compile_c_files() {
    local directory="$1"
    echo "Compiling .c files to .so files in '$COMPILED_CODE_SOURCE_DIRECTORY'..."

    find "$directory" -name "*.c" | while read -r c_file; do
        # Get the relative path and create output directory
        relative_path="${c_file#$SOURCE_DIRECTORY/}"
        output_file_directory="$(dirname "$relative_path")"
        mkdir -p "$COMPILED_CODE_SOURCE_DIRECTORY/$output_file_directory"
        
        # Get the base name of the file without extension
        base_name=$(basename "$c_file" .c)
        
        # Compile to a .so file in the corresponding output directory
        gcc -shared -o "$COMPILED_CODE_SOURCE_DIRECTORY/$output_file_directory/$base_name.so" -fPIC $(python -m pybind11 --includes) "$c_file" || {
            echo "Error: Failed to compile '$c_file'"
            exit 1
        }
    done
}

# Function to copy necessary files to output directory
copy_files() {
    echo "Copying necessary files..."
    cp requirements.txt "$COMPILED_CODE_DIRECTORY" || { echo "Error: Failed to copy requirements.txt"; exit 1; }
    cp app.py "$COMPILED_CODE_DIRECTORY" || { echo "Error: Failed to copy app.py"; exit 1; }
    cp setup.sh "$COMPILED_CODE_DIRECTORY" || { echo "Error: Failed to copy setup.sh"; exit 1; }
    cp -r src/assets "$COMPILED_CODE_SOURCE_DIRECTORY" || { echo "Error: Failed to copy assets"; exit 1; }
    cp -r src/templates "$COMPILED_CODE_SOURCE_DIRECTORY" || { echo "Error: Failed to copy templates"; exit 1; }
    cp -r src/static "$COMPILED_CODE_SOURCE_DIRECTORY" || { echo "Error: Failed to copy static files"; exit 1; }
    cp -r src/scripts "$COMPILED_CODE_SOURCE_DIRECTORY" || { echo "Error: Failed to copy scripts"; exit 1; }
    cp prometheus_config/alert_rules.yml "$PROMETHEUS_OUTPUT_DIRECTORY/" || { echo "Error: Failed to copy Prometheus config"; exit 1; }
}

cleanup() {
    echo "Cleaning up temporary files..."
    find "$SOURCE_DIRECTORY" -name "*.c" -delete
    rm -rf build
}

# Main execution flow
mkdir -p "$COMPILED_CODE_SOURCE_DIRECTORY"
generate_c_files
# compile_c_files "$SOURCE_DIRECTORY"
# copy_files
# Uncomment to enable cleanup
# cleanup

echo "Build process completed successfully."

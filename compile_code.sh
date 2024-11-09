#!/bin/bash

# Define directories
ROOT_DIRECTORY=$(pwd)
SOURCE_DIRECTORY="$ROOT_DIRECTORY/src"
COMPILED_CODE_DIRECTORY="$ROOT_DIRECTORY/systemguard_compiled"
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
    python_files=($(find_python_files))
    local total_files=${#python_files[@]}
    local compiled_files=0
    counter=0

    for python_file in "${python_files[@]}"; do
        counter=$((counter + 1))
        echo "Processing $counter out of $total_files files: $python_file"
    
        # Add the language level directive if not present
        if ! grep -q "# cython: language_level=" "$python_file"; then
            echo "# cython: language_level=3" | cat - "$python_file" > temp && mv temp "$python_file"
        fi
        cython "$python_file" -o "${python_file%.py}.c" && compiled_files=$((compiled_files + 1)) || {
            echo "Error: Failed to generate C file for '$python_file'"
            exit 1
        }
    done

    echo "Generated $compiled_files out of $total_files C files."
}

# Function to compile .c files to .so files
compile_c_files() {
    local directory="$1"
    echo "Compiling .c files to .so files in '$COMPILED_CODE_SOURCE_DIRECTORY'..."
    
    local c_files=()
    while IFS= read -r -d '' c_file; do
        c_files+=("$c_file")
    done < <(find "$directory" -name "*.c" -print0)

    local total_files=${#c_files[@]}
    local compiled_files=0

    for c_file in "${c_files[@]}"; do
        # Get the relative path and create output directory
        relative_path="${c_file#$SOURCE_DIRECTORY/}"
        output_file_directory="$(dirname "$relative_path")"
        mkdir -p "$COMPILED_CODE_SOURCE_DIRECTORY/$output_file_directory"
        
        # Get the base name of the file without extension
        base_name=$(basename "$c_file" .c)
        
        # Compile to a .so file in the corresponding output directory
        gcc -shared -o "$COMPILED_CODE_SOURCE_DIRECTORY/$output_file_directory/$base_name.so" -fPIC $(python -m pybind11 --includes) "$c_file" && compiled_files=$((compiled_files + 1)) || {
            echo "Error: Failed to compile '$c_file'"
            exit 1
        }
    done

    echo "Compiled $compiled_files out of $total_files C files."
}

# Function to copy necessary files to output directory
copy_files() {
    echo "Copying necessary files..."
    cp requirements.txt "$COMPILED_CODE_DIRECTORY" || { echo "Error: Failed to copy requirements.txt"; exit 1; }
    cp systemguard.py "$COMPILED_CODE_DIRECTORY" || { echo "Error: Failed to copy app.py"; exit 1; }
    cp setup.sh "$COMPILED_CODE_DIRECTORY" || { echo "Error: Failed to copy setup.sh"; exit 1; }
    rsync -av --exclude='.initialized' src/assets "$COMPILED_CODE_SOURCE_DIRECTORY" || { echo "Error: Failed to copy assets"; exit 1; }
    cp -r src/templates "$COMPILED_CODE_SOURCE_DIRECTORY" || { echo "Error: Failed to copy templates"; exit 1; }
    cp -r src/static "$COMPILED_CODE_SOURCE_DIRECTORY" || { echo "Error: Failed to copy static files"; exit 1; }
    rsync -av --exclude='*.py' --exclude='*.c' src/scripts "$COMPILED_CODE_SOURCE_DIRECTORY" || { echo "Error: Failed to copy scripts"; exit 1; }
    cp prometheus_config/alert_rules.yml "$PROMETHEUS_OUTPUT_DIRECTORY/" || { echo "Error: Failed to copy Prometheus config"; exit 1; }
}

cleanup() {
    echo "Cleaning up temporary files..."
    find "$SOURCE_DIRECTORY" -name "*.c" -delete
    rm -rf build
}

# Main execution flow
mkdir -p "$COMPILED_CODE_SOURCE_DIRECTORY"
copy_files
generate_c_files
compile_c_files "$SOURCE_DIRECTORY"
# cleanup
# create logs directory in compiled code
mkdir -p "$COMPILED_CODE_DIRECTORY/logs"

echo "Build process completed successfully."

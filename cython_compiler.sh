#!/bin/bash

# Define directories
SRC_DIR="src"
COMPILED_CODE_DIR="compiled_code"
OUTPUT_DIR="$COMPILED_CODE_DIR/src"
C_OUTPUT_DIR="output/c_source"

# Function to find all .py files in the src directory
find_python_files() {
    python_files=()
    while IFS= read -r -d '' file; do
        python_files+=("$file")
    done < <(find "$SRC_DIR" -name '*.py' -print0)
    echo "${python_files[@]}"
}

# Function to compile .py files to .c files using Cython
generate_c_files() {
    echo "Generating C files from Python files..."
    python_files=$(find_python_files)
    python3 setup.py build_ext --inplace || {
        echo "Failed to generate C files"
        exit 0
    }
}

# Function to compile .c files to .so files
compile_c_files() {
    local dir="$1"
    echo "Compiling .c files to .so files in $dir..."

    find "$dir" -name "*.c" | while read -r c_file; do
        # Get the relative path and create output directory
        relative_path="${c_file#$SRC_DIR/}"
        output_file_dir="$(dirname "$relative_path")"
        mkdir -p "$OUTPUT_DIR/$output_file_dir"
        
        # Get the base name of the file without extension
        base_name=$(basename "$c_file" .c)
        
        # Compile to a .so file in the corresponding output directory
        gcc -shared -o "$OUTPUT_DIR/$output_file_dir/$base_name.so" -fPIC $(python3 -m pybind11 --includes) "$c_file" || {
            echo "Failed to compile $c_file"
            exit 1
        }
    done
}

# Function to copy necessary files to output directory
copy_files() {
    echo "Copying necessary files..."
    cp app.py $COMPILED_CODE_DIR || { echo "Failed to copy app.py"; exit 1; }
    cp -r src/assets "$OUTPUT_DIR" || { echo "Failed to copy assets"; exit 1; }
    cp -r src/templates "$OUTPUT_DIR" || { echo "Failed to copy templates"; exit 1; }
    cp -r src/static "$OUTPUT_DIR" || { echo "Failed to copy static"; exit 1; }
    cp -r src/scripts "$OUTPUT_DIR" || { echo "Failed to copy scripts"; exit 1; }
    cp .env "$COMPILED_CODE_DIR" || { echo "Failed to copy .env"; exit 1; }
    
}

# # Main execution flow
# mkdir -p "$OUTPUT_DIR"
# # generate_c_files
# compile_c_files "$SRC_DIR"
copy_files

echo "Build process completed successfully."

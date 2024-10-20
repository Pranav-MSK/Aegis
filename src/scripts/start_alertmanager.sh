#!/bin/bash

# Set strict error handling
set -euo pipefail
IFS=$'\n\t'

# Initialize TMP_FILE variable
TMP_FILE=""

# Function to log informational messages
log_info() {
    echo "[INFO] $1"
}

# Function to log error messages and exit
log_error() {
    echo "[ERROR] $1"
    exit 1
}

# Function to log warnings
log_warn() {
    echo "[WARN] $1"
}

# Function to cleanup temporary files
cleanup() {
    local exit_code=$?
    if [ -n "$TMP_FILE" ] && [ -f "$TMP_FILE" ]; then
        rm -f "$TMP_FILE"
        log_info "Cleaned up temporary file"
    fi
    if [ $exit_code -ne 0 ]; then
        log_error "Script failed with exit code $exit_code"
    fi
    exit $exit_code
}

# Set trap for cleanup
trap cleanup EXIT

# Function to validate YAML syntax
validate_yaml() {
    local yaml_file="$1"
    if command -v python3 >/dev/null 2>&1; then
        python3 -c "import yaml; yaml.safe_load(open('$yaml_file'))" 2>/dev/null || {
            log_error "Invalid YAML syntax in $yaml_file"
        }
    else
        log_warn "Python3 not found. Skipping YAML validation"
    fi
}

# Function to check if AlertManager is reachable
check_alertmanager() {
    local ip="$1"
    local port="$2"
    timeout 5 bash -c ">/dev/tcp/$ip/$port" 2>/dev/null || {
        log_warn "AlertManager not reachable at $ip:$port. Configuration will still be updated."
    }
}

# Function to create backup with timestamp
create_backup() {
    local config_file="$1"
    local backup_file="${config_file}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$config_file" "$backup_file" || {
        log_error "Failed to create backup at $backup_file"
    }
    log_info "Backup created at $backup_file"
}

# Function to check if alerting configuration exists
check_alerting_exists() {
    local config_file="$1"
    if grep -q "^alerting:" "$config_file"; then
        log_info "AlertManager configuration already exists"
        return 0
    fi
    return 1
}

# Main script starts here
main() {
    # Define script directory and configuration directory (two levels up)
    local SCRIPT_DIR
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)" || {
        log_error "Failed to determine script directory"
    }
    
    local CONFIG_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")/prometheus_config"
    local PROMETHEUS_CONFIG="$CONFIG_DIR/prometheus.yml"
    
    # Get IP address with error handling
    local SYSTEMGUARD_APP_IP
    SYSTEMGUARD_APP_IP=$(hostname -I | cut -d' ' -f1) || {
        log_error "Failed to determine system IP address"
    }
    
    if [ -z "$SYSTEMGUARD_APP_IP" ]; then
        log_error "Could not determine system IP address"
    fi
    
    local ALERTMANAGER_PORT="9093"

    # Validate directory and file existence
    if [ ! -d "$CONFIG_DIR" ]; then
        log_error "Configuration directory not found at $CONFIG_DIR"
    fi

    if [ ! -f "$PROMETHEUS_CONFIG" ]; then
        log_error "Prometheus configuration file not found at $PROMETHEUS_CONFIG"
    fi

    if [ ! -w "$PROMETHEUS_CONFIG" ]; then
        log_error "No write permission for $PROMETHEUS_CONFIG"
    fi

    # Validate existing configuration
    validate_yaml "$PROMETHEUS_CONFIG"

    # Check if alerting configuration already exists
    if check_alerting_exists "$PROMETHEUS_CONFIG"; then
        log_info "No changes needed. Exiting."
        exit 0
    fi

    # Check AlertManager accessibility
    check_alertmanager "$SYSTEMGUARD_APP_IP" "$ALERTMANAGER_PORT"

    # Create temporary file with error handling
    TMP_FILE=$(mktemp) || {
        log_error "Failed to create temporary file"
    }

    # Create backup before modifications
    create_backup "$PROMETHEUS_CONFIG"

    # Process the configuration file
    {
        local found_global=false
        while IFS= read -r line || [ -n "$line" ]; do
            echo "$line"
            
            # If we find the global section, add alerting config after it
            if [[ "$line" =~ ^global: ]] && [ "$found_global" = false ]; then
                found_global=true
                # Read until we find a line that doesn't start with whitespace
                while IFS= read -r subline || [ -n "$subline" ]; do
                    echo "$subline"
                    if [[ ! "$subline" =~ ^[[:space:]] ]]; then
                        # Add our alerting configuration before the next section
                        cat << EOF

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - ${SYSTEMGUARD_APP_IP}:${ALERTMANAGER_PORT}
      timeout: 5m
EOF
                        break
                    fi
                done
            fi
        done
    } < "$PROMETHEUS_CONFIG" > "$TMP_FILE" || {
        log_error "Failed to process configuration file"
    }

    # Validate new configuration before applying
    validate_yaml "$TMP_FILE"

    # Move temporary file to prometheus.yml
    mv "$TMP_FILE" "$PROMETHEUS_CONFIG" || {
        log_error "Failed to update configuration file"
    }

    log_info "Successfully updated alerting configuration in $PROMETHEUS_CONFIG"
}

# Execute main function
main
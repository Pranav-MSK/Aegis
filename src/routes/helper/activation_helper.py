import os
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import subprocess
import functools

number_of_sum_check_digits = 5

def calculate_checksum(unique_id, num_of_digits=2):
    """Calculate a simple checksum for the given unique ID."""
    checksum = sum((index + 1) * ord(char) for index, char in enumerate(unique_id))
    return checksum % (10 ** num_of_digits)

def get_os_installation_uuid():
    """Retrieve the OS installation UUID."""
    try:
        if os.path.exists('/etc/machine-id'):
            with open('/etc/machine-id', 'r') as f:
                return f.read().strip()
        elif os.path.exists('/var/lib/dbus/machine-id'):
            with open('/var/lib/dbus/machine-id', 'r') as f:
                return f.read().strip()
        else:
            return "OS Installation UUID not found."
    except Exception as e:
        return f"Error reading OS Installation UUID: {str(e)}"

def get_motherboard_serial(sudo_password):
    """Retrieve the motherboard serial number using sudo password."""
    try:
        command = f"echo {sudo_password} | sudo -S dmidecode -s baseboard-serial-number"
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return output.decode().strip()
    except subprocess.CalledProcessError as e:
        return "Error retrieving Motherboard Serial: " + e.output.decode().strip()
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@functools.lru_cache(maxsize=1)
def calculate_unique_system_id(sudo_password):
    """Calculate a unique system identifier using various hardware IDs."""
    os_uuid = get_os_installation_uuid()
    motherboard_serial = get_motherboard_serial(sudo_password)
    unique_id = f"{os_uuid}:{motherboard_serial}"
    unique_id = ''.join(e for e in unique_id if e.isalnum())
    checksum = calculate_checksum(unique_id, number_of_sum_check_digits)
    unique_id += f"{checksum}"
    return unique_id

def verify_activation_code(activation_code, hardware_id, secret_key):
    try:
        cipher = Fernet(secret_key)
        decrypted_data = cipher.decrypt(activation_code.encode()).decode()
        license_key, received_hardware_id = decrypted_data.split(':')
        
        if received_hardware_id == hardware_id:
            return True, license_key
        return False, None
    except Exception as e:
        return False, f"Error verifying activation code: {str(e)}"
    
def check_license_expiration(license_key, secret_key):
    cipher = Fernet(secret_key)
    decrypted_license_data = cipher.decrypt(license_key.encode()).decode()
    
    license_parts = decrypted_license_data.split('|')
    if len(license_parts) < 3:
        return False, "Invalid license format."

    plan_type = license_parts[0]
    expiration_date_str = license_parts[1]
    is_trial = license_parts[2]
    expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d')

    today = datetime.now()
    if today > expiration_date:
        return False, "License has expired."

    remaining_days = (expiration_date - today).days
    return True, remaining_days, plan_type, is_trial
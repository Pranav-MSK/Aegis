# cython: language_level=3
import os
import re
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

from src.helper import load_secret_key

number_of_sum_check_digits = 2
internal_license_key_path = os.path.join(os.path.expanduser('~'), '.database', 'internal_license_key.txt')

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


def calculate_unique_system_id():
    """
    Calculate a unique system identifier using the OS installation UUID.
    The ID is filtered to alphanumeric characters, downsampled, and includes a checksum.
    """
    os_uuid = get_os_installation_uuid()
    clean_uuid = re.sub(r'\W+', '', os_uuid)
    short_uuid = clean_uuid[::2]
    checksum = calculate_checksum(short_uuid, number_of_sum_check_digits)    
    return f"{short_uuid}{checksum}"


def verify_activation_code(activation_code, hardware_id, obfuscated_key):
    try:
        cipher = Fernet(obfuscated_key)
        decrypted_data = cipher.decrypt(activation_code.encode()).decode()
        license_key, received_hardware_id = decrypted_data.split(':')
        
        if received_hardware_id == hardware_id:
            return True, license_key
        return False, None
    except Exception as e:
        return False, f"Error verifying activation code: {str(e)}"
    
def check_license_expiration(license_key, obfuscated_key):
    base_plan = "Free Edition"
    is_trial = False
    max_scrap_target = 1
    max_alert_rules = 5
    max_number_of_graphs = 5
    monthly_alert_tickets_limit = 10
    max_users_allowed = 5
    cipher = Fernet(obfuscated_key)
    decrypted_license_data = cipher.decrypt(license_key.encode()).decode()
    
    license_parts = decrypted_license_data.split('|')
    if len(license_parts) < 3:
        return False, "Invalid license format.", base_plan, is_trial, max_scrap_target, max_alert_rules, max_number_of_graphs, monthly_alert_tickets_limit, max_users_allowed

    plan_type = license_parts[0]
    expiration_date_str = license_parts[1]
    is_trial = license_parts[2]
    max_scrap_target = license_parts[3]
    max_alert_rules = license_parts[4]
    max_number_of_graphs = license_parts[5]
    monthly_alert_tickets_limit = license_parts[6]
    max_users_allowed = license_parts[7]

    expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d')

    today = datetime.now() + timedelta(days=0)
    expiration_date_str = expiration_date.strftime('%Y-%m-%d')
    if today >= expiration_date:
        return False, "License has expired {}. Please renew the license.".format(expiration_date_str), base_plan, is_trial, max_scrap_target, max_alert_rules, max_number_of_graphs, monthly_alert_tickets_limit, max_users_allowed

    remaining_plan_days = (expiration_date - today).days
    return True, remaining_plan_days, plan_type, is_trial, max_scrap_target, max_alert_rules, max_number_of_graphs, monthly_alert_tickets_limit, max_users_allowed

def get_plan_details():
    obfuscated_key = load_secret_key("obfuscation.so")
    is_plan_not_expired = False
    remaining_plan_days = 0
    plan_type = "Free Edition"
    is_trial = False
    license_key = ""
    activation_code = ""
    systemguard_unique_id = calculate_unique_system_id()
    max_scrap_target = 1
    max_alert_rules = 5
    max_number_of_graphs = 5
    monthly_alert_tickets_limit = 10
    max_users_allowed = 5
    try:
        with open(internal_license_key_path, 'r') as f:
            license_data = f.read()
            license_key = license_data.split('\n')[1].split(':')[1]
            activation_code = license_data.split('\n')[2].split(':')[1]
            systemguard_unique_id = license_data.split('\n')[3].split(':')[1]

            is_valid, _ = verify_activation_code(activation_code, systemguard_unique_id, obfuscated_key)
            if not is_valid:
                return {
                    "is_plan_not_expired": is_plan_not_expired,
                    "remaining_plan_days": remaining_plan_days,
                    "plan_type": plan_type,
                    "is_trial": is_trial,
                    "license_key": license_key,
                    "activation_code": activation_code,
                    "systemguard_unique_id": systemguard_unique_id,
                    "max_scrap_target": max_scrap_target,
                    "max_alert_rules": max_alert_rules,
                    "max_number_of_graphs": max_number_of_graphs,
                    "monthly_alert_tickets_limit": monthly_alert_tickets_limit,
                    "max_users_allowed": max_users_allowed
                }


            is_plan_not_expired, remaining_plan_days, plan_type, is_trial, \
                max_scrap_target, max_alert_rules, max_number_of_graphs, \
                    monthly_alert_tickets_limit, max_users_allowed = check_license_expiration(license_key, obfuscated_key)
            if not is_plan_not_expired:
                return {
                        "is_plan_not_expired": is_plan_not_expired,
                        "remaining_plan_days": remaining_plan_days,
                        "plan_type": plan_type,
                        "is_trial": is_trial,
                        "license_key": license_key,
                        "activation_code": activation_code,
                        "systemguard_unique_id": systemguard_unique_id,
                        "max_scrap_target": max_scrap_target,
                        "max_alert_rules": max_alert_rules,
                        "max_number_of_graphs": max_number_of_graphs,
                        "monthly_alert_tickets_limit": monthly_alert_tickets_limit,
                        "max_users_allowed": max_users_allowed

                    }
            else:
                return {
                        "is_plan_not_expired": is_plan_not_expired,
                        "remaining_plan_days": remaining_plan_days,
                        "plan_type": plan_type,
                        "is_trial": is_trial,
                        "license_key": license_key,
                        "activation_code": activation_code,
                        "systemguard_unique_id": systemguard_unique_id,
                        "max_scrap_target": max_scrap_target,
                        "max_alert_rules": max_alert_rules,
                        "max_number_of_graphs": max_number_of_graphs,
                        "monthly_alert_tickets_limit": monthly_alert_tickets_limit,
                        "max_users_allowed": max_users_allowed
                    }
    except FileNotFoundError:
        return {
            "is_plan_not_expired": is_plan_not_expired,
            "remaining_plan_days": remaining_plan_days,
            "plan_type": plan_type,
            "is_trial": is_trial,
            "license_key": license_key,
            "activation_code": activation_code,
            "systemguard_unique_id": systemguard_unique_id,
            "max_scrap_target": max_scrap_target,
            "max_alert_rules": max_alert_rules,
            "max_number_of_graphs": max_number_of_graphs,
            "monthly_alert_tickets_limit": monthly_alert_tickets_limit,
            "max_users_allowed": max_users_allowed
        }

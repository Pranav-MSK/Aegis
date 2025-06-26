# cython: language_level=3
import os
import re
import requests
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
from src.helper.secrets import load_secret_key
from src.helper.basic_info import generate_unique_id
from src.schemas import LicenseInfo
# --- Constants ---

LICENSE_PATH = os.path.join(os.path.expanduser('~'), '.database', 'internal_license_key.txt')


# --- Cipher Utility ---
class LicenseCipher:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)

    def decrypt(self, token: str) -> str:
        return self.cipher.decrypt(token.encode()).decode()

    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()


# --- License Manager ---
class LicenseManager:
    def __init__(self, key_path: str = "obfuscation.so"):
        self.secret_key = load_secret_key(key_path)
        if self.secret_key is None:
            raise ValueError("Secret key cannot be None.")
        self.cipher = LicenseCipher(self.secret_key)

    def verify_activation_code(self, activation_code: str, expected_id: str) -> bool:
        try:
            license_key, received_id = self.cipher.decrypt(activation_code).split(":")
            return received_id == expected_id
        except Exception:
            return False
        
    def get_license_key(self, activation_code: str) -> str:
        try:
            decrypted = self.cipher.decrypt(activation_code)
            return decrypted.split(":")[0]
        except Exception as e:
            raise ValueError(f"Failed to decrypt activation code: {e}")

    def parse_license_data(self, encrypted_license: str) -> list:
        try:
            decrypted = self.cipher.decrypt(encrypted_license)
            parts = decrypted.split('|')
            if len(parts) < 8:
                raise ValueError("Incomplete license data.")
            return parts
        except Exception as e:
            raise ValueError(f"Failed to parse license: {e}")

    @staticmethod
    def get_google_server_time():
        try:
            response = requests.head("https://www.google.com", timeout=5)
            date_str = response.headers['Date']  # e.g., 'Fri, 14 Jun 2025 16:43:12 GMT'
            return datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S GMT')
        except Exception as e:
            print(f"Error fetching Google server time: {e}")
            return None
        
    def apply_license_plan(self, info: LicenseInfo, parts: list):
        exp_date = datetime.strptime(parts[1], '%Y-%m-%d')
        today = self.get_google_server_time() or datetime.utcnow()

        info.plan_type = parts[0]
        info.is_trial = parts[2] == "True"
        info.max_scrap_target = int(parts[3])
        info.max_alert_rules = int(parts[4])
        info.max_number_of_graphs = int(parts[5])
        info.monthly_alert_tickets_limit = int(parts[6])
        info.max_users_allowed = int(parts[7])

        if today >= exp_date:
            info.message = f"License expired on {exp_date.strftime('%Y-%m-%d')}"
            info.is_plan_not_expired = False
        else:
            info.remaining_plan_days = (exp_date - today).days
            info.is_plan_not_expired = True

    def load_license_info(self, path: str = LICENSE_PATH) -> LicenseInfo:
        info = LicenseInfo()
        try:
            with open(path) as f:
                lines = f.read().splitlines()
                if len(lines) < 4:
                    raise ValueError("Incomplete license file.")

                info.license_key = lines[1].split(':', 1)[1]
                info.activation_code = lines[2].split(':', 1)[1]
                info.systemguard_unique_id = lines[3].split(':', 1)[1]

                if not self.verify_activation_code(info.activation_code, info.systemguard_unique_id):
                    info.message = "Invalid activation code"
                    return info

                license_parts = self.parse_license_data(info.license_key)
                self.apply_license_plan(info, license_parts)

        except FileNotFoundError:
            info.message = "License file not found."
        except Exception as e:
            info.message = str(e)

        return info


# --- Public API ---
def get_plan_details():
    return LicenseManager().load_license_info().to_dict()

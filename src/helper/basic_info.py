# cython: language_level=3
import os
from pathlib import Path
import re
import subprocess
from functools import lru_cache
SUM_CHECK_DIGITS = 2

ROOT_DIR = Path(__file__).resolve().parents[2]

@lru_cache(maxsize=128)
def get_basic_system_information():
    return {
        "system_username": os.getlogin(),
        "nodename": os.uname().nodename,
    }

def get_system_node_name():
    return os.uname().nodename

def get_ip_address():
    try:
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, check=True)
        return result.stdout.split()[0]
    except (IndexError, subprocess.CalledProcessError):
        return None

def get_os_installation_uuid():
    for path in ['/etc/machine-id', '/var/lib/dbus/machine-id']:
        try:
            if os.path.exists(path):
                with open(path) as f:
                    return f.read().strip()
        except Exception:
            pass
    return "OS Installation UUID not found."


def calculate_checksum(data: str, digits: int = 2) -> int:
    return sum((i + 1) * ord(c) for i, c in enumerate(data)) % (10 ** digits)


def generate_unique_id() -> str:
    uuid = get_os_installation_uuid()
    cleaned = re.sub(r'\W+', '', uuid)
    short = cleaned[::2]
    return f"{short}{calculate_checksum(short, SUM_CHECK_DIGITS)}"


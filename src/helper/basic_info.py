import os
import subprocess
from functools import lru_cache

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

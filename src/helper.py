# cython: language_level=3
import os
import ctypes
import subprocess
from functools import lru_cache


CURR_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURR_DIR)

def load_library(filename):
    try:
        lib_path = os.path.join(ROOT_DIR, "src/toolkit")
        lib = ctypes.CDLL(os.path.join(lib_path, filename))
        return lib
    except OSError as e:
        raise

def retrieve_obfuscated_key(key_name):
    library = load_library(key_name)
    library.get_obfuscated_key.restype = ctypes.c_char_p
    obfuscated_key = library.get_obfuscated_key()
    return obfuscated_key.decode()

@lru_cache(maxsize=128)
def get_basic_system_information():
    """
    Get basic system information.
    ---
    Parameters:
    ---
    Returns:
        dict: Basic system information.
    """
    system_info = {
        "system_username": os.getlogin(),
        "nodename": os.uname().nodename,
    }
    return system_info

def get_system_username():
    """
    Get the current system username.
    ---
    Parameters:
    ---
    Returns:
        str: System username.
    """
    return os.getlogin()

def get_system_node_name():
    """ 
    Get the system node name.
    ---
    Parameters:
    ---
    Returns:
        str: System node name
    """
    return os.uname().nodename

def get_ip_address():
    try:
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, check=True)
        ip_address = result.stdout.split()[0]
        return ip_address
    except (IndexError, subprocess.CalledProcessError) as e:
        return None

def check_installation_information():
    # Output dictionary to store results
    output = {
        "is_git_repo": False,
        "git_branch": None,
        "git_commit": None,
        "git_repo": None,
        "last_commit_date": None,
        "last_commit_message": None,
        "update_available": False
    }

    # Check if .git directory exists
    if not os.path.isdir(".git"):
        return output

    # Read the HEAD file to get the current branch
    try:
        with open(".git/HEAD", "r") as f:
            head = f.read().strip()
    except IOError:
        return output

    # Check if HEAD is a branch
    if head.startswith("ref: refs/heads/"):
        branch = head.replace("ref: refs/heads/", "")
        output["is_git_repo"] = True
        output["git_branch"] = branch

    # Get the last commit information
    try:
        result = subprocess.run(["git", "log", "-1", "--pretty=format:%H|%ad|%s", "--date=short"], capture_output=True, text=True, check=True)
        commit_data = result.stdout.split("|")
        output["git_commit"] = commit_data[0]
        output["last_commit_date"] = commit_data[1]
        output["last_commit_message"] = commit_data[2]
    except subprocess.CalledProcessError:
        pass

    # Check for updates
    try:
        result = subprocess.run(["git", "status", "-uno"], capture_output=True, text=True, check=True)
        if "Your branch is up to date" in result.stdout:
            output["update_available"] = False
        else:
            output["update_available"] = True
    except subprocess.CalledProcessError:
        pass

    return output

def load_secret_key(key_name):
    """Load the secret key for the application."""
    try:
        obfuscated_key = retrieve_obfuscated_key(key_name)
        if obfuscated_key:
            return obfuscated_key
    except Exception as e:
        raise RuntimeError(f"An error occurred while reading the secret key: {e}")


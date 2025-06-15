import os
import ctypes
from pathlib import Path
from src.helper.basic_info import ROOT_DIR

def load_library(filename):
    try:
        lib_path = os.path.join(ROOT_DIR, "src/toolkit")
        return ctypes.CDLL(os.path.join(lib_path, filename))
    except OSError as e:
        raise

def retrieve_obfuscated_key(key_name):
    library = load_library(key_name)
    library.get_obfuscated_key.restype = ctypes.c_char_p
    return library.get_obfuscated_key().decode()

import os
import ctypes
from src.helper import load_library

CURR_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(CURR_DIR)

# Load the shared library
logger_lib = load_library(os.path.join(ROOT_DIR, 'src/toolkit/logger.so'))

# Define the function prototype
logger_lib.log_message.argtypes = [ctypes.c_char_p, ctypes.c_char_p]

class Logger:
    def __init__(self):
        pass

    def log_message(self, level, message):
        """General logger function."""
        logger_lib.log_message(level.encode('utf-8'), message.encode('utf-8'))

    def info(self, message):
        """Log an info message."""
        self.log_message("INFO", message)

    def debug(self, message):
        """Log a debug message."""
        self.log_message("DEBUG", message)

    def warn(self, message):
        """Log a warning message."""
        self.log_message("WARNING", message)

    def error(self, message):
        """Log an error message."""
        self.log_message("ERROR", message)

# Create an instance of the Logger
logger = Logger()

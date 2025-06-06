# cython: language_level=3
import logging
import os
from pathlib import Path

# /hom/<user>/logs/
HOME_LOGS_DIR = Path.home() / "logs"
# Ensure the logs directory exists
HOME_LOGS_DIR.mkdir(parents=True, exist_ok=True)

def get_logger(name: str = __name__):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent adding multiple handlers to the same logger
    if not logger.handlers:
        log_dir = HOME_LOGS_DIR
        os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(f"{log_dir}/systemGuard_log.txt", mode='a')
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger
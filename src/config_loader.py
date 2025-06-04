# cython: language_level=3
import configparser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def load_config(file_path: Path) -> configparser.ConfigParser:
    """Load configuration from config.ini file."""
    config = configparser.ConfigParser()
    config.read(file_path)
    
    return config

config_file = ROOT_DIR / 'src' / 'config.ini'
configuration_settings = load_config(config_file)

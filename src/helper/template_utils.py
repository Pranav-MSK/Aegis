# cython: language_level=3
import os
from jinja2 import Environment, FileSystemLoader


from src.helper.logger import get_logger
from src.config.config_loader import configuration_settings

logger = get_logger(__name__)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

cache = {}

CACHE_EXPIRATION = configuration_settings.getint("metrics.settings", "CACHE_EXPIRATION")
DIVIDE_BY_1024 = configuration_settings.getboolean("metrics.settings", "DIVIDE_BY_1024")

CONVERSION_FACTOR_MB = 1024**2 if DIVIDE_BY_1024 else 1000**2
CONVERSION_FACTOR_GB = 1024**3 if DIVIDE_BY_1024 else 1000**3
domain_name = "google.com"


def render_template_from_file(template_file_path, **context):
    """Renders a Jinja template from a file with the given context and returns the rendered HTML content."""
    template_dir = os.path.dirname(template_file_path)
    template_file = os.path.basename(template_file_path)

    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_file)

    return template.render(**context)


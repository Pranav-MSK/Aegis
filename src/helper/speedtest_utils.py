
# cython: language_level=3
import os
import subprocess

from src.helper.logger import get_logger
from src.config.config_loader import configuration_settings

logger = get_logger(__name__)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_speedtest():
    """Run a speed test using speedtest-cli."""
    try:
        result = subprocess.run(
            ["speedtest-cli"], capture_output=True, text=True, check=True
        )
        output_lines = result.stdout.splitlines()
        download_speed = upload_speed = ping = None

        for line in output_lines:
            if "Download:" in line:
                download_speed = line.split("Download: ")[1]
            elif "Upload:" in line:
                upload_speed = line.split("Upload: ")[1]
            elif "Ping:" in line:
                ping = line.split("Ping: ")[1]

        return {
            "download_speed": download_speed,
            "upload_speed": upload_speed,
            "ping": ping,
            "status": "Success",
        }

    except subprocess.CalledProcessError as e:
        return {"status": "Error", "message": e.stderr}

    except Exception as e:
        return {"status": "Error", "message": str(e)}


def format_speed(speed):
    """Format the speed in appropriate units."""
    if speed < 1000:
        return f"{speed:.2f} Bytes/s"
    elif speed < 1000**2:
        return f"{speed / 1000:.2f} KB/s"
    else:
        return f"{speed / (1000 ** 2):.2f} MB/s"


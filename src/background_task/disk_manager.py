import psutil
import threading
import time

CONVERSION_FACTOR_GB = 1024 ** 3  # Convert bytes to gigabytes

def format_speed(bytes_per_sec):
    """Format speed from bytes per second to a more readable format."""
    if bytes_per_sec < 1024:
        return f"{bytes_per_sec} B/s"
    elif bytes_per_sec < 1024 ** 2:
        return f"{bytes_per_sec / 1024:.2f} KB/s"
    elif bytes_per_sec < 1024 ** 3:
        return f"{bytes_per_sec / (1024 ** 2):.2f} MB/s"
    else:
        return f"{bytes_per_sec / (1024 ** 3):.2f} GB/s"

class DiskMetrics:
    def __init__(self):
        self.metrics = {}
        self.running = True
        self.update_thread = threading.Thread(target=self.update_metrics)
        self.update_thread.start()

    def update_metrics(self):
        initial_io = psutil.disk_io_counters()
        while self.running:
            time.sleep(1)  # Collect metrics every second
            final_io = psutil.disk_io_counters()
            disk_info = psutil.disk_usage('/')

            # Calculate read/write speeds
            read_per_sec = final_io.read_bytes - initial_io.read_bytes
            write_per_sec = final_io.write_bytes - initial_io.write_bytes
            
            self.metrics = {
                'disk_percent': round(disk_info.percent, 2),
                'disk_total': round(disk_info.total / CONVERSION_FACTOR_GB, 1),
                'disk_used': round(disk_info.used / CONVERSION_FACTOR_GB, 1),
                'disk_free': round(disk_info.free / CONVERSION_FACTOR_GB, 1),
                'disk_read': format_speed(final_io.read_bytes),
                'disk_write': format_speed(final_io.write_bytes),
                'disk_read_per_sec': format_speed(read_per_sec),
                'disk_write_per_sec': format_speed(write_per_sec)
            }
            initial_io = final_io  # Reset initial values for the next iteration

    def stop(self):
        self.running = False
        self.update_thread.join()

# Usage
# disk_metrics = DiskMetrics()
# Access disk_metrics.metrics whenever you need the latest data

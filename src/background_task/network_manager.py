import psutil
import threading
import time

DIVIDE_BY_1024 = False
CONVERSION_FACTOR_MB = (1024 ** 2) if DIVIDE_BY_1024 else (1000 ** 2)
CONVERSION_FACTOR_GB = (1024 ** 3) if DIVIDE_BY_1024 else (1000 ** 3)

def format_speed(speed):
    """Format the speed in appropriate units."""
    if speed < 1024:
        return f"{speed:.2f} Bytes/s"
    elif speed < 1024 ** 2:
        return f"{speed / 1024:.2f} KB/s"
    else:
        return f"{speed / (1024 ** 2):.2f} MB/s"

class NetworkMetrics:
    def __init__(self):
        self.metrics = {}
        self.running = True
        self.update_thread = threading.Thread(target=self.update_metrics)
        self.update_thread.start()

    def update_metrics(self):
        initial_net_io = psutil.net_io_counters()
        while self.running:
            time.sleep(1)  # Collect metrics every second
            final_net_io = psutil.net_io_counters()
            self.metrics = {
                'network_sent': round(final_net_io.bytes_sent / CONVERSION_FACTOR_MB, 2),
                'network_received': round(final_net_io.bytes_recv / CONVERSION_FACTOR_MB, 2),
                'upload_speed': format_speed(final_net_io.bytes_sent - initial_net_io.bytes_sent),
                'download_speed': format_speed(final_net_io.bytes_recv - initial_net_io.bytes_recv),
            }
            initial_net_io = final_net_io  # Reset initial values for the next iteration

    def stop(self):
        self.running = False
        self.update_thread.join()

# Usage
# network_metrics = NetworkMetrics()
# Call network_metrics.metrics whenever you need the latest data

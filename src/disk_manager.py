# cython: language_level=3
"""
DiskMetrics: A thread-safe disk monitoring utility that tracks disk usage and I/O performance.
Provides real-time metrics including disk usage, read/write speeds, and space utilization.
"""

import psutil
import threading
import time
from typing import Dict, Union
from dataclasses import dataclass
from contextlib import contextmanager
from src.config_loader import configuration_settings

# Constants
BYTES_PER_GB = configuration_settings.getint('metrics.settings', 'BYTES_PER_GB')
BYTES_PER_MB = configuration_settings.getint('metrics.settings', 'BYTES_PER_MB')
BYTES_PER_KB = configuration_settings.getint('metrics.settings', 'BYTES_PER_KB')
UPDATE_INTERVAL = configuration_settings.getfloat('metrics.settings', 'UPDATE_INTERVAL')

@dataclass
class IOStats:
    """Container for I/O statistics."""
    read_bytes: int
    write_bytes: int
    read_speed: float
    write_speed: float

def format_speed(bytes_per_sec: float) -> str:
    """
    Format speed from bytes per second to human-readable format.
    
    Args:
        bytes_per_sec: Speed in bytes per second
        
    Returns:
        str: Formatted string with appropriate unit (B/s, KB/s, MB/s, or GB/s)
    """
    if bytes_per_sec < BYTES_PER_KB:
        return f"{bytes_per_sec:.2f} B/s"
    elif bytes_per_sec < BYTES_PER_MB:
        return f"{bytes_per_sec / BYTES_PER_KB:.2f} KB/s"
    elif bytes_per_sec < BYTES_PER_GB:
        return f"{bytes_per_sec / BYTES_PER_MB:.2f} MB/s"
    return f"{bytes_per_sec / BYTES_PER_GB:.2f} GB/s"

class DiskMetricsError(Exception):
    """Base exception for DiskMetrics-related errors."""
    pass

class DiskMetrics:
    """
    Thread-safe disk metrics monitor that continuously tracks disk usage and I/O statistics.
    
    Attributes:
        path (str): Mount point to monitor (default: '/')
        update_interval (float): Time between metric updates in seconds
    """
    
    def __init__(self, path: str = '/', update_interval: float = UPDATE_INTERVAL):
        """Initialize the DiskMetrics monitor."""
        self.path = path
        self.update_interval = update_interval
        self._metrics: Dict[str, Union[float, str]] = {}
        self._running = False
        self._lock = threading.Lock()
        self._thread: Union[threading.Thread, None] = None
        
    def start(self) -> None:
        """Start the metrics monitoring thread."""
        if self._running:
            raise DiskMetricsError("Monitor is already running")
        
        self._running = True
        self._thread = threading.Thread(target=self._update_metrics, daemon=True)
        self._thread.start()
        
    def stop(self) -> None:
        """Stop the metrics monitoring thread."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join()
            self._thread = None
            
    @contextmanager
    def run_context(self):
        """Context manager for running the monitor."""
        try:
            self.start()
            yield self
        finally:
            self.stop()
            
    def _calculate_io_stats(self, initial, final) -> IOStats:
        """Calculate I/O statistics between two measurements."""
        read_diff = final.read_bytes - initial.read_bytes
        write_diff = final.write_bytes - initial.write_bytes
        
        return IOStats(
            read_bytes=final.read_bytes,
            write_bytes=final.write_bytes,
            read_speed=read_diff / self.update_interval,
            write_speed=write_diff / self.update_interval
        )
        
    def _update_metrics(self) -> None:
        """Update disk metrics in a continuous loop."""
        try:
            initial_io = psutil.disk_io_counters()
            
            while self._running:
                time.sleep(self.update_interval)
                
                # Collect current metrics
                final_io = psutil.disk_io_counters()
                disk_usage = psutil.disk_usage(self.path)
                io_stats = self._calculate_io_stats(initial_io, final_io)
                
                # Update metrics thread-safely
                with self._lock:
                    self._metrics = {
                        'disk_percent': round(disk_usage.percent, 2),
                        'disk_total_gb': round(disk_usage.total / BYTES_PER_GB, 1),
                        'disk_used_gb': round(disk_usage.used / BYTES_PER_GB, 1),
                        'disk_free_gb': round(disk_usage.free / BYTES_PER_GB, 1),
                        'disk_read_total': format_speed(io_stats.read_bytes),
                        'disk_write_total': format_speed(io_stats.write_bytes),
                        'disk_read_speed': format_speed(io_stats.read_speed),
                        'disk_write_speed': format_speed(io_stats.write_speed)
                    }                
                initial_io = final_io
                
        except Exception as e:
            self._running = False
            raise DiskMetricsError(f"Error updating metrics: {str(e)}")

    @property 
    def get_metrics(self) -> Dict[str, Union[float, str]]:
        """
        Get current disk metrics.
        
        Returns:
            dict: Current disk metrics including usage and I/O statistics
        """
        with self._lock:
            return self._metrics.copy()
            
    @property
    def disk_percent(self) -> float:
        """Disk usage percentage."""
        return float(self._metrics.get('disk_percent', 0.0))
        
    @property
    def disk_total_gb(self) -> float:
        """Total disk space in GB."""
        return float(self._metrics.get('disk_total_gb', 0.0))
        
    @property
    def disk_used_gb(self) -> float:
        """Used disk space in GB."""
        return float(self._metrics.get('disk_used_gb', 0.0))
        
    @property
    def disk_free_gb(self) -> float:
        """Free disk space in GB."""
        return float(self._metrics.get('disk_free_gb', 0.0))
        
    @property
    def disk_read_total(self) -> str:
        """Total bytes read, formatted."""
        return str(self._metrics.get('disk_read_total', '0 B/s'))
        
    @property
    def disk_write_total(self) -> str:
        """Total bytes written, formatted."""
        return str(self._metrics.get('disk_write_total', '0 B/s'))
        
    @property
    def disk_read_speed(self) -> str:
        """Current read speed, formatted."""
        return str(self._metrics.get('disk_read_speed', '0 B/s'))
        
    @property
    def disk_write_speed(self) -> str:
        """Current write speed, formatted."""
        return str(self._metrics.get('disk_write_speed', '0 B/s'))
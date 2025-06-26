# cython: language_level=3
"""
NetworkMetrics: A thread-safe network monitoring utility that tracks network usage and speeds.
Provides real-time metrics including bytes sent/received and upload/download speeds.
"""

import psutil
import threading
import time
from typing import Dict, Union, NamedTuple
from dataclasses import dataclass
from contextlib import contextmanager
from src.core.config.config_loader import configuration_settings
from src.schemas import NetworkStats

# Constants
BYTES_PER_MB_BINARY = 1024 ** 2  # Binary megabyte (MiB)
BYTES_PER_MB_DECIMAL = 1000 ** 2  # Decimal megabyte (MB)
BYTES_PER_KB = configuration_settings.getint('metrics.settings', 'BYTES_PER_KB')  # Kilobyte (KB)
UPDATE_INTERVAL = configuration_settings.getfloat('metrics.settings', 'UPDATE_INTERVAL')

class SpeedUnits(NamedTuple):
    """Network speed formatting thresholds and labels."""
    threshold: int
    divisor: float
    unit: str

SPEED_UNITS = [
    SpeedUnits(BYTES_PER_MB_BINARY, BYTES_PER_MB_BINARY, "MB/s"),
    SpeedUnits(BYTES_PER_KB, BYTES_PER_KB, "KB/s"),
    SpeedUnits(0, 1, "Bytes/s")
]


class NetworkMetricsError(Exception):
    """Base exception for NetworkMetrics-related errors."""
    pass

def format_speed(speed: float, use_binary: bool = True) -> str:
    """
    Format network speed to human-readable format.
    
    Args:
        speed: Speed in bytes per second
        use_binary: If True, use binary units (1024), else decimal (1000)
        
    Returns:
        str: Formatted string with appropriate unit
    """
    try:
        for unit in SPEED_UNITS:
            if speed >= unit.threshold:
                return f"{speed / unit.divisor:.2f} {unit.unit}"
        return f"{speed:.2f} Bytes/s"
    except Exception as e:
        raise NetworkMetricsError(f"Error formatting speed: {str(e)}")

class NetworkMetrics:
    """
    Thread-safe network metrics monitor that continuously tracks network usage and speeds.
    
    Attributes:
        use_binary_units (bool): Use binary (1024) or decimal (1000) units for MB conversion
        update_interval (float): Time between metric updates in seconds
    """
    
    def __init__(self, use_binary_units: bool = True, update_interval: float = UPDATE_INTERVAL):
        """Initialize the NetworkMetrics monitor."""
        self.use_binary_units = use_binary_units
        self.update_interval = update_interval
        self._metrics: Dict[str, Union[float, str]] = {}
        self._running = False
        self._lock = threading.Lock()
        self._thread: Union[threading.Thread, None] = None
        self._conversion_factor = BYTES_PER_MB_BINARY if use_binary_units else BYTES_PER_MB_DECIMAL
        
    def start(self) -> None:
        """Start the metrics monitoring thread."""
        if self._running:
            raise NetworkMetricsError("Monitor is already running")
        
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
            
    def _calculate_network_stats(self, initial, final) -> NetworkStats:
        """Calculate network statistics between two measurements."""
        upload_speed = (final.bytes_sent - initial.bytes_sent) / self.update_interval
        download_speed = (final.bytes_recv - initial.bytes_recv) / self.update_interval
        
        return NetworkStats(
            bytes_sent=final.bytes_sent,
            bytes_recv=final.bytes_recv,
            upload_speed=upload_speed,
            download_speed=download_speed
        )
        
    def _update_metrics(self) -> None:
        """Update network metrics in a continuous loop."""
        try:
            initial_net_io = psutil.net_io_counters()
            
            while self._running:
                time.sleep(self.update_interval)
                
                # Collect current metrics
                final_net_io = psutil.net_io_counters()
                stats = self._calculate_network_stats(initial_net_io, final_net_io)
                
                # Update metrics thread-safely
                with self._lock:
                    self._metrics = {
                        'network_sent_mb': round(stats.bytes_sent / self._conversion_factor, 2),
                        'network_received_mb': round(stats.bytes_recv / self._conversion_factor, 2),
                        'upload_speed': format_speed(stats.upload_speed, self.use_binary_units),
                        'download_speed': format_speed(stats.download_speed, self.use_binary_units),
                        'upload_speed_raw': stats.upload_speed,
                        'download_speed_raw': stats.download_speed
                    }
                
                initial_net_io = final_net_io
                
        except Exception as e:
            self._running = False
            raise NetworkMetricsError(f"Error updating metrics: {str(e)}")
    
    @property
    def get_metrics(self) -> Dict[str, Union[float, str]]:
        """Get all current network metrics."""
        with self._lock:
            return self._metrics.copy()
    
    @property
    def network_sent_mb(self):
        """Total megabytes sent."""
        with self._lock:
            return self._metrics.get('network_sent_mb', 0.0)
    
    @property
    def network_received_mb(self):
        """Total megabytes received."""
        with self._lock:
            return self._metrics.get('network_received_mb', 0.0)
    
    @property
    def upload_speed(self):
        """Current upload speed (formatted)."""
        with self._lock:
            return self._metrics.get('upload_speed', '0 Bytes/s')
    
    @property
    def download_speed(self):
        """Current download speed (formatted)."""
        with self._lock:
            return self._metrics.get('download_speed', '0 Bytes/s')
    
    @property
    def upload_speed_raw(self):
        """Current upload speed in bytes per second."""
        with self._lock:
            return self._metrics.get('upload_speed_raw', 0.0)
    
    @property
    def download_speed_raw(self):
        """Current download speed in bytes per second."""
        with self._lock:
            return self._metrics.get('download_speed_raw', 0.0)

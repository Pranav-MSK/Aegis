# cython: language_level=3
from src.services.security.network_helper import handle_network_scan, handle_port_scan

class SecurityScanService:
    def handle_network_scan(self):
        return handle_network_scan()

    def handle_port_scan(self):
        return handle_port_scan()

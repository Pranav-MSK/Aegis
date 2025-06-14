from src.routes.helper.network_helper import handle_network_scan, handle_port_scan

class SecurityScanService:
    def handle_network_scan(self):
        return handle_network_scan()

    def handle_port_scan(self):
        return handle_port_scan()

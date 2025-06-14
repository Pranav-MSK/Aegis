# cython: language_level=3
import subprocess
from threading import Lock


class PortManager:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        """
        Note: Deisgn pattern: Singleton
        Ensure that only one instance of PortManager exists (Singleton pattern).
        This method is thread-safe to prevent multiple instances in a multi-threaded environment.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(PortManager, cls).__new__(cls)
            return cls._instance

    def reset_sudo_timestamp(self):
        """
        Reset the sudo timestamp to force password prompt on next sudo command.
        """
        subprocess.run(['sudo', '-k'])

    def list_open_ports(self, sudo_password: str):
        """
        List all open TCP and UDP ports using iptables.

        :param sudo_password: The sudo password used to run the iptables command.
        :return: A list of open ports and an error message if applicable.
        """
        try:
            result = subprocess.run(
                ['sudo', '-S', 'iptables', '-L', '-n'],
                input=f"{sudo_password}\n",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if "incorrect password" in result.stderr.lower():
                return [], "Incorrect sudo password. Please try again."

            open_ports = []
            for line in result.stdout.splitlines():
                if "ACCEPT" in line:
                    if 'tcp' in line:
                        open_ports.append(('TCP', line))
                    elif 'udp' in line:
                        open_ports.append(('UDP', line))
            return open_ports, ""
        except Exception as e:
            return [], str(e)

    def enable_port(self, port: str, protocol: str, sudo_password: str):
        """
        Enable a port using iptables.

        :param port: Port number
        :param protocol: 'tcp' or 'udp'
        :param sudo_password: sudo password
        :return: Success or error message
        """
        try:
            command = [
                'sudo', '-S', 'iptables', '-A', 'INPUT',
                '-p', protocol, '--dport', str(port), '-j', 'ACCEPT'
            ]
            result = subprocess.run(command, input=f'{sudo_password}\n', text=True)
            if result.returncode == 0:
                return f"Port {port}/{protocol.upper()} enabled."
            else:
                return result.stderr
        except Exception as e:
            return str(e)

    def disable_port(self, port: str, protocol: str, sudo_password: str):
        """
        Disable a port using iptables.

        :param port: Port number
        :param protocol: 'tcp' or 'udp'
        :param sudo_password: sudo password
        :return: Success or error message
        """
        try:
            command = [
                'sudo', '-S', 'iptables', '-D', 'INPUT',
                '-p', protocol, '--dport', str(port), '-j', 'ACCEPT'
            ]
            result = subprocess.run(command, input=f'{sudo_password}\n', text=True)
            if result.returncode == 0:
                return f"Port {port}/{protocol.upper()} disabled."
            else:
                return result.stderr
        except Exception as e:
            return str(e)

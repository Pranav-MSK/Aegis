import subprocess
from src.helper.system_metrics import get_top_processes
from src.helper.logger import get_logger

logger = get_logger(__name__)

class ProcessService:
    @staticmethod
    def get_processes(number_of_processes, sort_by="cpu", order="asc"):
        top_processes = get_top_processes(number_of_processes)
        sort_key = {
            "cpu": 1,
            "memory": 2,
            "name": 0,
        }.get(sort_by, 1)
        top_processes.sort(key=lambda x: x[sort_key], reverse=(order == "desc"))
        return top_processes

    @staticmethod
    def kill_process(pid_to_kill, process_name, sudo_password, user=None, remote_addr=None):
        log_context = (f" by user '{user}' (IP: {remote_addr})" if user and remote_addr else "")
        try:
            result = subprocess.run(
                ['sudo', '-S', 'kill', str(pid_to_kill)],
                input=sudo_password + '\n',
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                # Try SIGKILL
                result = subprocess.run(
                    ['sudo', '-S', 'kill', '-9', str(pid_to_kill)],
                    input=sudo_password + '\n',
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            if result.returncode == 0:
                logger.info(f"Killed process '{process_name}' (PID {pid_to_kill}) successfully{log_context}")
                return True, f"Process '{process_name}' (PID {pid_to_kill}) killed successfully."
            else:
                # Check if process exists
                check_process = subprocess.run(
                    ['ps', '-p', str(pid_to_kill)],
                    capture_output=True,
                    text=True
                )
                if check_process.returncode != 0:
                    logger.info(f"Process '{process_name}' (PID {pid_to_kill}) no longer exists. Assumed terminated.{log_context}")
                    return True, f"Process '{process_name}' (PID {pid_to_kill}) no longer exists. It may have been terminated."
                else:
                    logger.error(f"Failed to kill process '{process_name}' (PID {pid_to_kill}). Error: {result.stderr.strip()}{log_context}")
                    return False, f"Failed to kill process '{process_name}' (PID {pid_to_kill}). Error: {result.stderr.strip()}"
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout while attempting to kill process '{process_name}' (PID {pid_to_kill}).{log_context}")
            return False, f"Timeout while attempting to kill process '{process_name}' (PID {pid_to_kill})."
        except Exception as e:
            logger.error(f"Error executing command to kill process '{process_name}' (PID {pid_to_kill}): {str(e)}{log_context}")
            return False, f"Error executing command: {str(e)}"
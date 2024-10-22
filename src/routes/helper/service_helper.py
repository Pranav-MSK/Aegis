# cython: language_level=3
from datetime import datetime
from http.client import HTTPException
import psutil
from typing import Dict, List, Any, Union
import docker
import traceback

# Type aliases
ContainerMetrics = Dict[str, Any]

class ServiceMonitor:
    def __init__(self):
        self.service_patterns = {
            "Python": [
                "python",
                "python3",
                "gunicorn",
                "uvicorn",
                "django",
                "celery",
                "flask",
                "fastapi",
                "supervisord",
                "jupyter",
                "ipython",
                "uwsgi",
                "daphne",
                "pylint",
                "pip",  # Added
                "anaconda",  # Added
            ],
            "Java": [
                "java",
                "javaw",
                "tomcat",
                "spring",
                "gradle",
                "maven",
                "jenkins",
                "cassandra",
                "kafka",
                "zookeeper",
                "elasticsearch",
                "jboss",
                "wildfly",
                "weblogic",
                "jetty",
                "scala",  # Added
                "groovy",  # Added
            ],
            "Node.js": [
                "node",
                "npm",
                "yarn",
                "pnpm",
                "nodemon",
                "pm2",
                "forever",
                "nest",
                "nuxt",
                "next",
                "gatsby",
                "electron",
                "gulp",  # Added
                "grunt",  # Added
            ],
            "Go": [
                "go",
                "gofmt",
                "godoc",
                "gcloud",
                "beego",
                "gin-gonic",
                "hugo",
                "prometheus",
                "grafana",
                "go get",  # Added
            ],
            "Databases": [
                "mysql",
                "mysqld",
                "postgres",
                "postgresql",
                "mongodb",
                "mongod",
                "redis",
                "redis-server",
                "elasticsearch",
                "cassandra",
                "couchdb",
                "mariadb",
                "influxd",
                "cockroach",
                "clickhouse",
                "neo4j",
                "sqlite",
                "rethinkdb",
                "etcd",
                "sqlserver",  # Added
                "firebase",  # Added
            ],
            "Web Servers": [
                "nginx",
                "apache2",
                "httpd",
                "apache",
                "lighttpd",
                "caddy",
                "traefik",
                "haproxy",
                "varnish",
                "squid",
                "lightspeed",  # Added
                "iis",  # Added
            ],
            "Message Queues": [
                "rabbitmq",
                "kafka",
                "activemq",
                "celery",
                "redis",
                "mosquitto",
                "zeromq",
                "nats-server",
                "sqs",  # Added
                "mqtt",  # Added
            ],
            "Docker": [
                "docker",
                "containerd",
                "dockerd",
                "docker-compose",
                "docker-proxy",
                "buildkit",
                "containerd-shim",
                "kaniko",  # Added
            ],
            "Kubernetes": [
                "kubelet",
                "kube-proxy",
                "kube-apiserver",
                "kube-scheduler",
                "kube-controller",
                "etcd",
                "coredns",
                "flannel",
                "calico",
                "helm",  # Added
                "kubectl",  # Added
            ],
            "CI/CD": [
                "jenkins",
                "gitlab-runner",
                "github-runner",
                "teamcity",
                "bamboo",
                "travis",
                "circleci",
                "argocd",
                "tekton",
                "spinnaker",  # Added
            ],
            "Monitoring": [
                "prometheus",
                "grafana",
                "node_exporter",
                "telegraf",
                "collectd",
                "datadog",
                "zabbix",
                "nagios",
                "sensu",
                "influxd",
                "elasticsearch",
                "newrelic",  # Added
                "appdynamics",  # Added
            ],
            "Security": [
                "fail2ban",
                "ufw",
                "iptables",
                "selinux",
                "apparmor",
                "clamav",
                "snort",
                "suricata",
                "ossec",  # Added
                "tripwire",  # Added
            ],
            "Load Balancers": [
                "haproxy",
                "nginx",
                "traefik",
                "envoy",
                "kong",
                "ambassador",
                "istio-proxy",
                "f5",  # Added
            ],
            "Caching": [
                "redis",
                "memcached",
                "varnish",
                "squid",
                "couchbase",  # Added
            ],
            "Development Tools": [
                "git",
                "svn",
                "mercurial",
                "vscode",
                "idea",
                "sublime_text",
                "atom",
                "postman",
                "docker-compose",  # Added
                "vagrant",  # Added
            ],
            "Suspect Programs": [  # New key for suspect services
                "malware",  # Example, add actual suspect service names
                "keylogger",
                "spyware",
                "rootkit",
                "ransomware",
                "backdoor",
                "trojan",
                "adware",
                "phishing",
            ],
        }

    def get_process_info(self, proc: psutil.Process) -> Dict[str, Any]:
        """Get relevant information about a process."""
        try:
            with proc.oneshot():
                created_time = datetime.fromtimestamp(proc.create_time())
                uptime = datetime.now() - created_time

                return {
                    "pid": proc.pid,
                    "name": proc.name(),
                    "cmd": " ".join(proc.cmdline())[:100] if proc.cmdline() else "",
                    "status": proc.status(),
                    "cpu": round(proc.cpu_percent(), 2),
                    "memory_mb": round(proc.memory_info().rss / (1024 * 1024), 2),
                    "ports": self.get_process_ports(proc),
                    "created_time": created_time.isoformat(),
                    "uptime_seconds": int(uptime.total_seconds()),
                    "uptime_human": self.format_uptime(uptime),
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return {}

    def get_process_ports(self, proc: psutil.Process) -> List[int]:
        """Get ports used by the process."""
        try:
            connections = proc.net_connections(kind="inet")
            return sorted(
                list(
                    set(
                        conn.laddr.port
                        for conn in connections
                        if hasattr(conn, "laddr") and conn.laddr and conn.laddr.port
                    )
                )
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return []

    def get_running_services(self) -> Dict[str, Any]:
        """Get information about running services grouped by type."""
        timestamp = datetime.now().isoformat()
        services = {category: [] for category in self.service_patterns.keys()}
        summary = {
            category: {"count": 0, "total_memory_mb": 0}
            for category in self.service_patterns.keys()
        }

        try:
            for proc in psutil.process_iter(["name", "cmdline"]):
                try:
                    proc_name = proc.name().lower()
                    cmdline = " ".join(proc.cmdline()).lower() if proc.cmdline() else ""

                    for category, patterns in self.service_patterns.items():
                        if any(
                            pattern.lower() in proc_name or pattern.lower() in cmdline
                            for pattern in patterns
                        ):
                            proc_info = self.get_process_info(proc)
                            if proc_info:
                                services[category].append(proc_info)
                                summary[category]["count"] += 1
                                summary[category]["total_memory_mb"] += proc_info[
                                    "memory_mb"
                                ]
                            break

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    continue

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        # Round summary memory values
        for category in summary:
            summary[category]["total_memory_mb"] = round(
                summary[category]["total_memory_mb"], 2
            )

        return {"timestamp": timestamp, "services": services, "summary": summary}

    def format_uptime(self, uptime) -> str:
        """Format uptime duration to readable string."""
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m {seconds}s"


# ------------------------------------------------------------------------------------------------------------------------
# docker container helper



def format_bytes(bytes_value: Union[int, float, str]) -> str:
    """
    Format bytes into human readable format.
    
    Args:
        bytes_value (Union[int, float, str]): Number of bytes
        
    Returns:
        str: Formatted string with appropriate unit
    """
    try:
        # Convert string to float if necessary
        if isinstance(bytes_value, str):
            bytes_value = float(bytes_value)
        bytes_value = float(bytes_value)  # Ensure float type
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024
        return f"{bytes_value:.2f} TB"
    except (ValueError, TypeError):
        return "0.00 B"

def safe_int_convert(value: Union[int, str, float]) -> int:
    """
    Safely convert a value to integer.
    
    Args:
        value (Union[int, str, float]): Value to convert
        
    Returns:
        int: Converted integer value
    """
    try:
        if isinstance(value, str):
            # Remove any non-numeric characters
            value = ''.join(c for c in value if c.isdigit() or c == '.')
        return int(float(value))
    except (ValueError, TypeError):
        return 0

def calculate_cpu_percent(stats: dict) -> float:
    """
    Calculate CPU percentage in a more robust way.
    
    Args:
        stats (dict): Container stats from Docker API
        
    Returns:
        float: CPU usage percentage
    """
    try:
        cpu_count = safe_int_convert(stats['cpu_stats'].get('online_cpus', 1))
        
        cpu_delta = safe_int_convert(stats['cpu_stats']['cpu_usage']['total_usage']) - \
                   safe_int_convert(stats['precpu_stats']['cpu_usage']['total_usage'])
                   
        system_delta = safe_int_convert(stats['cpu_stats']['system_cpu_usage']) - \
                      safe_int_convert(stats['precpu_stats']['system_cpu_usage'])
        
        if system_delta > 0:
            cpu_percent = (cpu_delta / system_delta) * 100.0 * cpu_count
            return round(cpu_percent, 2)
        return 0.0
    except KeyError:
        return 0.0

def format_container_creation_time(created_str):
    """Convert the container creation timestamp to a formatted string."""
    try:
        created_time = datetime.strptime(created_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")
        now = datetime.utcnow()
        diff = now - created_time

        seconds = diff.total_seconds()
        minutes = seconds // 60
        hours = minutes // 60
        days = hours // 24
        months = days // 30
        years = days // 365

        if years >= 1:
            return f"{int(years)} year{'s' if years > 1 else ''} ago"
        elif months >= 1:
            return f"{int(months)} month{'s' if months > 1 else ''} ago"
        elif days >= 1:
            return f"{int(days)} day{'s' if days > 1 else ''} ago"
        elif hours >= 1:
            return f"{int(hours)} hour{'s' if hours > 1 else ''} ago"
        elif minutes >= 1:
            return f"{int(minutes)} minute{'s' if minutes > 1 else ''} ago"
        else:
            return f"{int(seconds)} second{'s' if seconds > 1 else ''} ago"
    except ValueError as e:
        print(f"Error formatting container creation time: {e}")
        return "Unknown"

def get_running_docker_containers() -> List[ContainerMetrics]:
    """
    Get metrics for all running Docker containers.
    
    Returns:
        List[ContainerMetrics]: List of container metrics dictionaries
    """
    try:
        client = docker.from_env()
        containers = []
        
        for container in client.containers.list():
            try:
                stats = container.stats(stream=False)
                
                # Calculate CPU percentage using the more robust method
                cpu_percent = calculate_cpu_percent(stats)
                
                # Calculate memory usage with proper error handling
                try:
                    memory_usage = safe_int_convert(stats['memory_stats'].get('usage', 0))
                    memory_limit = safe_int_convert(stats['memory_stats'].get('limit', 1))
                    memory_percent = (memory_usage / memory_limit) * 100.0 if memory_limit > 0 else 0
                except KeyError:
                    memory_usage = 0
                    memory_percent = 0
                
                # Get network stats if available
                network_stats = {
                    'rx_bytes': 0,
                    'tx_bytes': 0
                }
                
                if 'networks' in stats:
                    for interface in stats['networks'].values():
                        network_stats['rx_bytes'] += safe_int_convert(interface.get('rx_bytes', 0))
                        network_stats['tx_bytes'] += safe_int_convert(interface.get('tx_bytes', 0))
                
                containers.append({
                    'name': container.name,
                    'id': container.id[:12],  # Short ID
                    'status': container.status,
                    'image': container.image.tags[0] if container.image.tags else 'none',
                    'created': format_container_creation_time(container.attrs['Created']),
                    'cpu_percent': cpu_percent,
                    'memory': {
                        'usage': format_bytes(memory_usage),
                        'percent': round(memory_percent, 2)
                    },
                    'network': {
                        'received': format_bytes(network_stats['rx_bytes']),
                        'transmitted': format_bytes(network_stats['tx_bytes'])
                    }
                })
            except Exception as e:
                tb = traceback.format_exc()
                print(f"Error collecting metrics for container {container.name} at line {tb.splitlines()[-3].strip()}: {e}")
                continue
                
        return containers
    except Exception as e:
        print(f"Error connecting to Docker: {e}")
        return []

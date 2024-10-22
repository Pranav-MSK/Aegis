# cython: language_level=3
from datetime import datetime
from http.client import HTTPException
import psutil
from datetime import datetime
from typing import Dict, List, Any


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
            ],
            "Docker": [
                "docker",
                "containerd",
                "dockerd",
                "docker-compose",
                "docker-proxy",
                "buildkit",
                "containerd-shim",
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
            ],
            "Load Balancers": [
                "haproxy",
                "nginx",
                "traefik",
                "envoy",
                "kong",
                "ambassador",
                "istio-proxy",
            ],
            "Caching": ["redis", "memcached", "varnish", "squid"],
            "Development Tools": [
                "git",
                "svn",
                "mercurial",
                "vscode",
                "idea",
                "sublime_text",
                "atom",
                "postman",
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

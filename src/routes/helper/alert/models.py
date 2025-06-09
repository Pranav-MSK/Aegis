from dataclasses import dataclass

@dataclass
class AlertMessage:
    alert_name: str
    alert_status: str
    instance: str
    severity: str
    description: str
    summary: str
    system_username: str
    system_hostname: str
    fingerprint: str
    runbook_url: str

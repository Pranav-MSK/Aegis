# cython: language_level=3
from dataclasses import dataclass, asdict

# schemas and models are different concepts(in this project), schemas are used for data validation and serialization
# while models are used for database interactions.

@dataclass
class UserNotification:
    """ 
    UserNotification schema for system notifications. 
    This schema is used to create a notification that can be displayed in the application.

    Attributes:
        type (str): The type of notification (e.g., "info", "warning", "error").
        icon (str): The icon to display with the notification.
        title (str): The title of the notification.
        message (str): The message content of the notification.
        is_global (bool): Whether the notification is global or user-specific.
        user_id (int | None): The ID of the user to whom the notification is directed, if applicable.
    """
    type: str
    icon: str
    title: str
    message: str
    is_global: bool = False
    user_id: int | None = None

@dataclass
class LicenseInfo:
    """
    LicenseInfo schema for storing license and plan details.
    This schema is used to represent the license information of the product.

    Attributes:
        plan_type (str): The type of plan the user is subscribed to.
        is_trial (bool): Indicates if the user is on a trial plan.
        remaining_plan_days (int): Number of days remaining in the current plan.
        is_plan_not_expired (bool): Indicates if the plan has not expired.
        license_key (str): The license key for the product.
        activation_code (str): The activation code used to activate the product.
        systemguard_unique_id (str): Unique identifier for the system guard.
        max_scrap_target (int): Maximum number of scrap targets allowed.
        max_alert_rules (int): Maximum number of alert rules allowed.
        max_number_of_graphs (int): Maximum number of graphs allowed.
        monthly_alert_tickets_limit (int): Monthly limit for alert tickets.
        max_users_allowed (int): Maximum number of users allowed in the plan.
        message (str): Additional message or information regarding the license.
    """

    plan_type: str = "Free Edition"
    is_trial: bool = False
    remaining_plan_days: int = 0
    is_plan_not_expired: bool = False
    license_key: str = ""
    activation_code: str = ""
    systemguard_unique_id: str = ""
    max_scrap_target: int = 1
    max_alert_rules: int = 5
    max_number_of_graphs: int = 5
    monthly_alert_tickets_limit: int = 10
    max_users_allowed: int = 5
    message: str = ""

    def to_dict(self):
        return asdict(self)

@dataclass
class AlertMessage:
    """
    AlertMessage schema for representing alert notifications.

    This schema is used to structure the data for alert notifications that are sent to users by the alert manager.

    """
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

@dataclass
class IOStats:
    """Container for I/O statistics."""
    read_bytes: int
    write_bytes: int
    read_speed: float
    write_speed: float


@dataclass
class NetworkStats:
    """Container for network statistics."""
    bytes_sent: int
    bytes_recv: int
    upload_speed: float
    download_speed: float

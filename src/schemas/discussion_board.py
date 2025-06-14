from dataclasses import dataclass

@dataclass
class UserNotification:
    type: str
    icon: str
    title: str
    message: str
    is_global: bool = False
    user_id: int | None = None

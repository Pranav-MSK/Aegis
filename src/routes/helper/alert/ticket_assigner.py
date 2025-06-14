# cython: language_level=3
from src.logger import get_logger
logger = get_logger(__name__)
from src.models import (
    AlertTicket,
    UserProfile,
)
from src.routes.helper.alert.quota_guard import can_create_alert
from schemas.alerts import AlertMessage


def create_alert_ticket(alert_instance: AlertMessage):
    """
    Saves the alert data to the database.

    Args:
        alert_name (str): Name of the alert.
        instance (str): Instance generating the alert.
        severity (str): Severity level of the alert.
        description (str): Detailed alert description.
        summary (str): Brief alert summary.
    """
    # Fetch all supervisors with user_level "admin"
    all_supervisors = UserProfile.query.filter_by(
        user_level="admin", assign_tickets=True
    ).all()

    if not can_create_alert():
        logger.warning("Monthly alert ticket limit reached. Ignoring the alert.")
        return

    if not all_supervisors:
        assigned_supervisor_id = None
        logger.warning("No supervisors available to assign.")
    else:
        # Load calculation for each supervisor
        supervisor_loads = {
            supervisor.id: AlertTicket.query.filter(
                AlertTicket.assigned_supervisor_id == supervisor.id,
                AlertTicket.ticket_status.in_(["Open", "In Progress"]),
            ).count()
            for supervisor in all_supervisors
        }
        logger.info(f"Supervisor loads: {supervisor_loads}")

        # Find the supervisor(s) with the minimum load
        min_load = min(supervisor_loads.values())
        eligible_supervisors = [
            supervisor_id
            for supervisor_id, load in supervisor_loads.items()
            if load == min_load
        ]

        # If there's a tie, use round-robin logic based on the last assigned supervisor
        last_assigned_supervisor = AlertTicket.query.order_by(
            AlertTicket.id.desc()
        ).first()
        last_assigned_supervisor_id = (
            last_assigned_supervisor.assigned_supervisor_id
            if last_assigned_supervisor
            else None
        )

        if last_assigned_supervisor_id in eligible_supervisors:
            # Continue from the last assigned supervisor
            last_index = eligible_supervisors.index(last_assigned_supervisor_id)
            next_index = (last_index + 1) % len(eligible_supervisors)
            assigned_supervisor_id = eligible_supervisors[next_index]
        else:
            # Assign the first eligible supervisor
            assigned_supervisor_id = eligible_supervisors[0]

    # Create and save the alert ticket
    alert_ticket = AlertTicket(
        alert_name=alert_instance.alert_name, # type: ignore    
        alert_status=alert_instance.alert_status, # type: ignore    
        instance=alert_instance.instance, # type: ignore    
        severity=alert_instance.severity, # type: ignore    
        summary=alert_instance.summary, # type: ignore    
        description=alert_instance.description, # type: ignore    
        assigned_supervisor_id=assigned_supervisor_id, # type: ignore    
        system_username=alert_instance.system_username, # type: ignore    
        system_hostname=alert_instance.system_hostname, # type: ignore    
        fingerprint=alert_instance.fingerprint, # type: ignore    
        runbook_url=alert_instance.runbook_url, # type: ignore    
    )
    alert_ticket.save()
    logger.info(f"Saving alert ticket: {alert_ticket}")


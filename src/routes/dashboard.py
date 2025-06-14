# cython: language_level=3
# Import necessary libraries
from flask import render_template, Blueprint, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, case

from src.config.app_config import app, csrf, get_app_info
from src.models import UserProfile, AlertTicket, ChartConfiguration, InstanceMetadata
from src.helper.utils import fetch_system_metrics
from src.core.activator import get_plan_details
from src.routes.helper.prometheus_helper import (
    count_of_targets, 
    calculate_total_rules, 
    retrieve_active_alertmanagers
)
dashboard_bp = Blueprint("dashboard", __name__)

def fetch_statistics(user_id):
    user_stats, ticket_stats, chart_stats, top_alert_tickets = (
        UserProfile.query.with_entities(
            func.count().label('total_users'),
            func.sum(case((UserProfile.is_active == True, 1), else_=0)).label('active_users'), # type: ignore
            func.sum(case((UserProfile.is_active == False, 1), else_=0)).label('inactive_users'), # type: ignore
            func.sum(case((UserProfile.user_level == 'admin', 1), else_=0)).label('admin_users'),
            func.sum(case((UserProfile.user_level == 'user', 1), else_=0)).label('regular_users'),
        ).first(),
        
        AlertTicket.query.with_entities(
            func.count().label('total_tickets'),
            func.sum(case((AlertTicket.ticket_status == 'Open', 1), else_=0)).label('open_tickets'),
            func.sum(case((AlertTicket.ticket_status == 'In Progress', 1), else_=0)).label('in_progress_tickets'),
            func.sum(case((AlertTicket.ticket_status == 'Resolved', 1), else_=0)).label('resolved_tickets'),
            func.sum(case((AlertTicket.ticket_status == 'Closed', 1), else_=0)).label('closed_tickets'),
            func.sum(case((AlertTicket.severity == 'critical', 1), else_=0)).label('critical_tickets'),
            func.sum(case((AlertTicket.severity == 'warning', 1), else_=0)).label('warning_tickets'),
            func.sum(case((AlertTicket.severity == 'info', 1), else_=0)).label('info_tickets'),
        ).first(),
        
        ChartConfiguration.query.with_entities(
            func.count().label('total_charts'),
            func.sum(case((ChartConfiguration.is_active == True, 1), else_=0)).label('active_charts')
        ).filter(ChartConfiguration.user_id == user_id).first(),

        AlertTicket.query.order_by(AlertTicket.created_at.desc()).limit(5).all()
    )

    return user_stats, ticket_stats, chart_stats, top_alert_tickets

@app.route("/", methods=["GET"])
@login_required
def dashboard():
    plan_details = get_plan_details()
    app.jinja_env.globals.update(
        is_plan_not_expired=plan_details.get('is_plan_not_expired'),
        remaining_plan_days=plan_details.get('remaining_plan_days'),
        plan_type=plan_details.get('plan_type'),
        is_trial=plan_details.get('is_trial'),
        license_key=plan_details.get('license_key'),
        activation_code=plan_details.get('activation_code'),
        systemguard_unique_id=plan_details.get('systemguard_unique_id'),
        max_scrap_target=plan_details.get('max_scrap_target'),
        max_alert_rules=plan_details.get('max_alert_rules'),
        max_number_of_graphs=plan_details.get('max_number_of_graphs'),
        monthly_alert_tickets_limit=plan_details.get('monthly_alert_tickets_limit'),
        max_users_allowed=plan_details.get('max_users_allowed')
    )

    system_info = fetch_system_metrics()

    user_stats, ticket_stats, chart_stats, top_alert_tickets = fetch_statistics(current_user.id)
    
    # Update system_info with gathered statistics
    system_info.update(user_stats._asdict()) # type: ignore
    system_info.update(ticket_stats._asdict()) # type: ignore
    system_info.update(chart_stats._asdict()) # type: ignore
    system_info["top_alert_tickets"] = top_alert_tickets
    
    # Prometheus metrics
    system_info["total_targets"] = count_of_targets()
    system_info["total_rules"] = calculate_total_rules()
    system_info["active_alertmanagers"] = retrieve_active_alertmanagers()
    instance_metadata = InstanceMetadata.to_dict(InstanceMetadata.query.first()) # type: ignore
    system_info['instance_metadata'] = instance_metadata
    
    return render_template("dashboard/homepage.html", system_info=system_info, current_user=current_user)

@app.route("/api/v1/dashboard/stats", methods=["GET"])
@login_required
@csrf.exempt
def api_dashboard_stats():
    user_stats, ticket_stats, chart_stats, top_alert_tickets = fetch_statistics(current_user.id)

    app_info = get_app_info()

    # Prepare the response data
    response_data = {
        "user_stats": user_stats._asdict(), # type: ignore
        "ticket_stats": ticket_stats._asdict(), # type: ignore
        "chart_stats": chart_stats._asdict(), # type: ignore
        "total_targets": count_of_targets(),
        "total_rules": calculate_total_rules(),
        "active_alertmanagers": retrieve_active_alertmanagers(),
        "max_scrap_target": app_info.get('max_scrap_target'),
        "max_alert_rules": app_info.get('max_alert_rules'),
        "max_number_of_graphs": app_info.get('max_number_of_graphs'),
        "monthly_alert_tickets_limit": app_info.get('monthly_alert_tickets_limit'),
        "max_users_allowed": app_info.get('max_users_allowed'),
        "top_alert_tickets": [ticket.to_dict() for ticket in top_alert_tickets],
    }

    return jsonify(response_data)

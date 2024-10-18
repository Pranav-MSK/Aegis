# cython: language_level=3
from flask import render_template, Blueprint
from flask_login import login_required, current_user
from sqlalchemy import func, case

from src.config import app, csrf
from src.models import UserProfile, AlertTicket, ChartConfiguration
from src.utils import get_system_info
from src.routes.helper.prometheus_helper import total_targets, total_rules, get_active_alert_manager

dashboard_bp = Blueprint("dashboard", __name__)

@app.route("/", methods=["GET"])
@login_required
def dashboard():
    system_info = get_system_info()

    # User statistics in a single query
    user_stats = UserProfile.query.with_entities(
        func.count().label('total_users'),
        func.sum(case((UserProfile.is_active == True, 1), else_=0)).label('active_users'),
        func.sum(case((UserProfile.user_level == 'admin', 1), else_=0)).label('admin_users'),
        func.sum(case((UserProfile.user_level == 'user', 1), else_=0)).label('regular_users'),
    ).first()
    system_info.update(user_stats._asdict())

    # Ticket statistics in a single query
    ticket_stats = AlertTicket.query.with_entities(
        func.count().label('total_tickets'),
        func.sum(case((AlertTicket.ticket_status == 'Open', 1), else_=0)).label('open_tickets'),
        func.sum(case((AlertTicket.ticket_status == 'In Progress', 1), else_=0)).label('in_progress_tickets'),
        func.sum(case((AlertTicket.ticket_status == 'Resolved', 1), else_=0)).label('resolved_tickets'),
        func.sum(case((AlertTicket.ticket_status == 'Closed', 1), else_=0)).label('closed_tickets'),
        func.sum(case((AlertTicket.severity == 'critical', 1), else_=0)).label('critical_tickets'),
        func.sum(case((AlertTicket.severity == 'warning', 1), else_=0)).label('warning_tickets'),
        func.sum(case((AlertTicket.severity == 'info', 1), else_=0)).label('info_tickets')
    ).first()
    system_info.update(ticket_stats._asdict())

    # Prometheus metrics
    system_info["total_targets"] = total_targets()
    system_info["total_rules"] = total_rules()
    system_info["active_alertmanagers"] = get_active_alert_manager()

       # number of chart 
    chart_stats = ChartConfiguration.query.with_entities(
        func.count().label('total_charts'),
        func.sum(case((ChartConfiguration.is_active == True, 1), else_=0)).label('active_charts')
    ).filter(ChartConfiguration.user_id == current_user.id).first()
    system_info.update(chart_stats._asdict())

    # Top 5 Alert Tickets
    top_alert_tickets = AlertTicket.query.order_by(AlertTicket.created_at.desc()).limit(8).all()
    system_info["top_alert_tickets"] = top_alert_tickets

    return render_template(
        "dashboard/alternative_homepage.html",
        system_info=system_info,
        current_user=current_user,
    )


from flask import jsonify

@app.route("/api/dashboard/stats", methods=["GET"])
@login_required
@csrf.exempt
def api_dashboard_stats():
    # User statistics in a single query
    user_stats = UserProfile.query.with_entities(
        func.count().label('total_users'),
        func.sum(case((UserProfile.is_active == True, 1), else_=0)).label('active_users'),
        func.sum(case((UserProfile.user_level == 'admin', 1), else_=0)).label('admin_users'),
        func.sum(case((UserProfile.user_level == 'user', 1), else_=0)).label('regular_users'),
    ).first()

    # Ticket statistics in a single query
    ticket_stats = AlertTicket.query.with_entities(
        func.count().label('total_tickets'),
        func.sum(case((AlertTicket.ticket_status == 'Open', 1), else_=0)).label('open_tickets'),
        func.sum(case((AlertTicket.ticket_status == 'In Progress', 1), else_=0)).label('in_progress_tickets'),
        func.sum(case((AlertTicket.ticket_status == 'Resolved', 1), else_=0)).label('resolved_tickets'),
        func.sum(case((AlertTicket.ticket_status == 'Closed', 1), else_=0)).label('closed_tickets'),
        func.sum(case((AlertTicket.severity == 'critical', 1), else_=0)).label('critical_tickets'),
        func.sum(case((AlertTicket.severity == 'warning', 1), else_=0)).label('warning_tickets'),
        func.sum(case((AlertTicket.severity == 'info', 1), else_=0)).label('info_tickets')
    ).first()

    chart_stats = ChartConfiguration.query.with_entities(
        func.count().label('total_charts'),
        func.sum(case((ChartConfiguration.is_active == True, 1), else_=0)).label('active_charts')
    ).filter(ChartConfiguration.user_id == current_user.id).first()

    # Prepare the response data
    response_data = {
        "user_stats": user_stats._asdict(),
        "ticket_stats": ticket_stats._asdict(),
        "total_targets": total_targets(),
        "total_rules": total_rules(),
        "chart_stats": chart_stats._asdict(),
        "active_alertmanagers": get_active_alert_manager(),
        "top_alert_tickets": [ticket.to_dict() for ticket in AlertTicket.query.order_by(AlertTicket.created_at.desc()).limit(5).all()]
    }

    return jsonify(response_data)

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user
from src.models import UserProfile
from src.routes.helper.common_helper import admin_required
from src.services.user_management_service import UserManagementService, ActivityService
from src.config.app_config import csrf, app

user_management_bp = Blueprint('user_management', __name__)
user_service = UserManagementService()
activity_service = ActivityService()

@app.route('/system/create_user', methods=['GET', 'POST'])
@admin_required
def create_user():
    if request.method == 'POST':
        success, message = user_service.create_user(request.form)
        flash(message, 'success' if success else 'danger')
        return redirect(url_for('user_management.view_users'))

    total_users = UserProfile.fetch_total_count()
    return render_template('users/create_user.html', total_users=total_users)


@app.route('/system/user_management', methods=['GET'])
@admin_required
def view_users():
    users = UserProfile.query.all()
    return render_template('users/view_users.html', users=users)


@app.route('/system/user/<username>', methods=['GET', 'POST'])
@admin_required
def update_user_profile(username):
    user = UserProfile.query.filter_by(username=username).first_or_404()
    if request.method == 'POST':
        user_service.update_user_profile(user, request.form)
        flash('User settings updated successfully!', 'success')
        return redirect(url_for('user_management.view_users'))
    return render_template('users/update_user.html', user=user)


@app.route('/delete_user/<username>', methods=['POST'])
@admin_required
def delete_user(username):
    user = UserProfile.query.filter_by(username=username).first_or_404()
    user_service.delete_user(user)
    flash(f'User {username} has been deleted successfully!', 'success')
    return redirect(url_for('user_management.view_users'))


@app.route("/system/activity_list", methods=["GET", "POST"])
@app.route("/system/activity_list/<int:activity_id>", methods=["GET", "PUT", "DELETE"])
@csrf.exempt
@admin_required
def manage_activities(activity_id=None):
    if request.method == "GET":
        if activity_id:
            activity = activity_service.get_activity(activity_id)
            return jsonify({
                "id": activity.id,
                "activity_name": activity.activity_name,
                "activity_point": activity.activity_point,
                "activity_description": activity.activity_description,
            })
        activities = activity_service.get_activities()
        return render_template("users/manage_activities.html", activities=activities)

    elif request.method == "POST":
        data = request.get_json()
        activity = activity_service.create_activity(data)
        return jsonify({"message": "Activity added successfully!", "success": True}), 201

    elif request.method == "PUT":
        data = request.get_json()
        activity = activity_service.get_activity(activity_id)
        activity_service.update_activity(activity, data)
        return jsonify({"message": "Activity updated successfully!", "success": True})

    elif request.method == "DELETE":
        activity = activity_service.get_activity(activity_id)
        activity_service.delete_activity(activity)
        return jsonify({"message": "Activity deleted successfully!", "success": True})

    return jsonify({"message": "Method Not Allowed", "success": False}), 405

# cython: language_level=3
from flask import render_template, redirect, url_for, request, flash, jsonify, Blueprint
from flask_login import login_required, current_user

from src.services.user.profile_service import ProfileService
from src.core.config.app_config import app

profile_bp = Blueprint('profile', __name__)

@app.route('/profile', methods=['GET'])
@login_required
def view_profile():
    user = current_user
    user.profile_picture_url = user.get_profile_picture_url()
    ticket_stats = ProfileService.get_ticket_stats(user)
    return render_template('users/view_profile.html', user=user, ticket_stats=ticket_stats)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        success, message = ProfileService.change_password(current_user, old_password, new_password, confirm_password)
        if not success:
            flash(message or 'An error occurred.', 'danger')
            return redirect(url_for('change_password'))
        flash('Password changed successfully!', 'success')
        return redirect(url_for('view_profile'))
    return render_template('users/change_password.html', user=current_user,
                            random_password=ProfileService.generate_random_password())

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = current_user
    if request.method == 'POST':
        ProfileService.update_profile(user, request.form)
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('view_profile'))
    return render_template('users/edit_profile.html', user=user)

@app.route('/system/delete_user', methods=['GET'])
@login_required
def delete_user_self():
    ProfileService.delete_user(current_user) # soft delete
    # If you want to hard delete, use ProfileService.hard_delete_user(current_user)

    flash('Your account has been deleted.', 'success')
    return redirect(url_for('login'))

@app.route("/api/v1/recent_activity", methods=["GET"])
@login_required
def get_activities():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    data = ProfileService.get_recent_activities(current_user.id, page, per_page)
    return jsonify(data), 200
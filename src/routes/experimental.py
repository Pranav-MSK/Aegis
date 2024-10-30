# cython: language_level=3
from flask import Blueprint, jsonify, request, render_template, flash
from sqlalchemy import desc

from functools import wraps
from flask_login import current_user, login_required
from src.config import app, db, csrf
from src.models.user_profile import UserActivity, UserProfile, ActivityTable
from src.routes.helper.common_helper import admin_required

experimental_bp = Blueprint('experimental', __name__)

# API Routes
@app.route('/api/v1/activities', methods=['GET'])
@login_required
def get_activities():
    """Get user's recent activities"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    user_points = UserProfile.query.get(current_user.id).user_points
    
    activities = UserActivity.query.filter_by(user_id=current_user.id)\
        .order_by(desc(UserActivity.created_at))\
        .paginate(page=page, per_page=per_page)

    return jsonify({
        'activities': [activity.to_dict() for activity in activities.items],
        'total': activities.total,
        'pages': activities.pages,
        'current_page': activities.page,
        'user_points': user_points
        
    }), 200

@app.route('/manage_activities', methods=['GET', 'POST'])
@app.route('/manage_activities/<int:activity_id>', methods=['GET', 'PUT', 'DELETE'])
@csrf.exempt
@admin_required
def manage_activities(activity_id=None):
    try:
        if request.method == 'GET':
            if activity_id:
                # Get single activity
                activity = ActivityTable.query.get_or_404(activity_id)
                return jsonify({
                    'id': activity.id,
                    'activity_name': activity.activity_name,
                    'activity_point': activity.activity_point,
                    'activity_description': activity.activity_description
                })
            else:
                # Get all activities
                activities = ActivityTable.query.all()
                return render_template('users/manage_activities.html', activities=activities)

        elif request.method == 'POST':
            data = request.get_json()
            new_activity = ActivityTable(
                activity_name=data['activity_name'],
                activity_point=data['activity_point'],
                activity_description=data['activity_description']
            )
            new_activity.save()
            return jsonify({"message": "Activity added successfully!", "success": True}), 201

        elif request.method == 'PUT':
            activity = ActivityTable.query.get_or_404(activity_id)
            data = request.get_json()
            
            activity.activity_name = data['activity_name']
            activity.activity_point = data['activity_point']
            activity.activity_description = data['activity_description']
            activity.save()
            return jsonify({"message": "Activity updated successfully!", "success": True})

        elif request.method == 'DELETE':
            activity = ActivityTable.query.get_or_404(activity_id)
            activity.delete()
            return jsonify({"message": "Activity deleted successfully!", "success": True})

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e), "success": False}), 400
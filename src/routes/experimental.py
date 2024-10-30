# cython: language_level=3
from flask import Blueprint, jsonify, request
from sqlalchemy import desc
from src.models.user_profile import Activity, UserProfile
from functools import wraps
from flask_login import current_user, login_required
from src.config import app

experimental_bp = Blueprint('experimental', __name__)

# API Routes
@app.route('/api/v1/activities', methods=['GET'])
@login_required
def get_activities():
    """Get user's recent activities"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    user_points = UserProfile.query.get(current_user.id).user_points
    
    activities = Activity.query.filter_by(user_id=current_user.id)\
        .order_by(desc(Activity.created_at))\
        .paginate(page=page, per_page=per_page)

    return jsonify({
        'activities': [activity.to_dict() for activity in activities.items],
        'total': activities.total,
        'pages': activities.pages,
        'current_page': activities.page,
        'user_points': user_points
        
    }), 200

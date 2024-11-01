# cython: language_level=3
from flask import render_template, blueprints

from src.config import app
from src.routes.helper.common_helper import admin_required

network_bp = blueprints.Blueprint('network', __name__)

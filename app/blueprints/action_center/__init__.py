from flask import Blueprint

action_center_bp = Blueprint('action_center', __name__, url_prefix='/action-center')

from app.blueprints.action_center import routes  # noqa

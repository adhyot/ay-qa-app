from flask import Blueprint

planning_bp = Blueprint('planning', __name__, url_prefix='/planning')

from app.blueprints.planning import routes  # noqa

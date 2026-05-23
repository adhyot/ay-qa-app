from flask import Blueprint

automation_bp = Blueprint('automation', __name__, url_prefix='/automation')

from app.blueprints.automation import routes  # noqa

from flask import Blueprint

execution_bp = Blueprint('execution', __name__, url_prefix='/execution')

from app.blueprints.execution import routes  # noqa

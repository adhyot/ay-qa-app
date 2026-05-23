from flask import Blueprint

core_bp = Blueprint('core', __name__)

from app.blueprints.core import routes  # noqa

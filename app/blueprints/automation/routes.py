from flask import render_template
from flask_login import login_required, current_user
from app.blueprints.automation import automation_bp
from app.models.integration import Integration
from app.models.test_case import TestSuite


@automation_bp.route('/')
@login_required
def index():
    return render_template('automation/index.html')


@automation_bp.route('/internal-tools')
@login_required
def internal_tools():
    integrations = Integration.query.filter_by(org_id=current_user.org_id, is_deleted=False).all()
    return render_template('automation/internal_tools.html', integrations=integrations)


@automation_bp.route('/framework')
@login_required
def framework():
    return render_template('automation/framework.html')

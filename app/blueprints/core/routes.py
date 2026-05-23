from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from app.blueprints.core import core_bp
from app.blueprints.core.helpers import get_dashboard_summary


@core_bp.route('/')
def index():
    return redirect(url_for('core.dashboard'))


@core_bp.route('/dashboard')
@login_required
def dashboard():
    summary = get_dashboard_summary(current_user.org_id) if current_user.org_id else {}
    return render_template('core/dashboard.html', summary=summary)


@core_bp.route('/health')
def health():
    return {'status': 'ok', 'service': 'qa-platform'}

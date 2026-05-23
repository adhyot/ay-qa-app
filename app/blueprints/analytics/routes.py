from flask import render_template
from flask_login import login_required
from app.blueprints.analytics import analytics_bp


@analytics_bp.route('/')
@login_required
def index():
    return render_template('analytics/index.html')


@analytics_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('analytics/dashboard.html')


@analytics_bp.route('/widget-library')
@login_required
def widget_library():
    return render_template('analytics/widget_library.html')


@analytics_bp.route('/reports')
@login_required
def reports():
    return render_template('analytics/reports.html')

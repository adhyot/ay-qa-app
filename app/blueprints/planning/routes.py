from flask import render_template
from flask_login import login_required, current_user
from app.blueprints.planning import planning_bp
from app.models.test_plan import Initiative, Release


@planning_bp.route('/')
@login_required
def index():
    return render_template('planning/index.html')


@planning_bp.route('/initiatives')
@login_required
def initiatives():
    all_initiatives = Initiative.query.filter_by(
        org_id=current_user.org_id, is_deleted=False
    ).order_by(Initiative.created_at.desc()).all()
    return render_template('planning/initiatives.html', initiatives=all_initiatives)


@planning_bp.route('/releases')
@login_required
def releases():
    all_releases = Release.query.filter_by(
        org_id=current_user.org_id, is_deleted=False
    ).order_by(Release.target_date.asc()).all()
    return render_template('planning/releases.html', releases=all_releases)

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.blueprints.action_center import action_center_bp
from app.extensions import db
from app.models.bug import Bug
from app.models.retro import SprintRetro, RetroActionItem
from app.models.allocation import Allocation


@action_center_bp.route('/')
@login_required
def index():
    return render_template('action_center/index.html')


@action_center_bp.route('/my-space')
@login_required
def my_space():
    my_bugs = Bug.query.filter_by(
        org_id=current_user.org_id, assigned_to=current_user.id, is_deleted=False
    ).order_by(Bug.created_at.desc()).all()
    return render_template('action_center/my_space.html', my_bugs=my_bugs)


@action_center_bp.route('/retro')
@login_required
def retro():
    retros = SprintRetro.query.filter_by(org_id=current_user.org_id, is_deleted=False)\
        .order_by(SprintRetro.date.desc()).all()
    return render_template('action_center/retro.html', retros=retros)


@action_center_bp.route('/retro/new', methods=['POST'])
@login_required
def new_retro():
    retro = SprintRetro(
        org_id=current_user.org_id,
        sprint_name=request.form.get('sprint_name'),
        sprint_number=request.form.get('sprint_number', type=int),
        created_by=current_user.id,
    )
    db.session.add(retro)
    db.session.commit()
    flash('Sprint retrospective started.', 'success')
    return redirect(url_for('action_center.retro'))


@action_center_bp.route('/allocation')
@login_required
def allocation():
    allocations = Allocation.query.filter_by(org_id=current_user.org_id, is_deleted=False)\
        .order_by(Allocation.artifact_type, Allocation.artifact_name).all()
    return render_template('action_center/allocation.html', allocations=allocations)

from flask import render_template, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.blueprints.execution import execution_bp
from app.models.test_run import TestRun, TestRunResult
from app.models.bug import Bug
from app.models.test_case import TestSuite


@execution_bp.route('/')
@login_required
def index():
    return redirect(url_for('execution.runs'))


@execution_bp.route('/runs')
@login_required
def runs():
    all_runs = TestRun.query.filter_by(org_id=current_user.org_id, is_deleted=False)\
        .order_by(TestRun.created_at.desc()).limit(50).all()
    suites = TestSuite.query.filter_by(org_id=current_user.org_id, is_deleted=False).all()
    return render_template('execution/runs.html', runs=all_runs, suites=suites)


@execution_bp.route('/runs/<run_id>')
@login_required
def run_detail(run_id):
    run = TestRun.query.filter_by(id=run_id, org_id=current_user.org_id).first_or_404()
    results = run.results.order_by(TestRunResult.started_at.asc()).all()
    return render_template('execution/run_detail.html', run=run, results=results)


@execution_bp.route('/runs/<run_id>/status')
@login_required
def run_status(run_id):
    run = TestRun.query.filter_by(id=run_id, org_id=current_user.org_id).first_or_404()
    return jsonify({
        'status': run.status,
        'pass_count': run.pass_count,
        'fail_count': run.fail_count,
        'total_count': run.total_count,
        'pass_rate': run.pass_rate,
    })


@execution_bp.route('/bugs')
@login_required
def bugs():
    from flask import request
    severity = request.args.get('severity')
    query = Bug.query.filter_by(org_id=current_user.org_id, is_deleted=False)
    if severity:
        query = query.filter_by(severity=severity)
    all_bugs = query.order_by(Bug.created_at.desc()).all()
    return render_template('execution/bugs.html', bugs=all_bugs, severity_filter=severity)


@execution_bp.route('/deployments')
@login_required
def deployments():
    return render_template('execution/deployments.html')

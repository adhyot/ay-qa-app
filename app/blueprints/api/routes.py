from flask import jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.blueprints.api import api_bp
from app.models.test_run import TestRun
from app.models.bug import Bug
from app.models.test_plan import Initiative
from app.models.simulator import SimulatorLog
from app.models.integration import Integration
from app.extensions import csrf

ACCESS_PIN = '0072'


# ── Auth ──────────────────────────────────────────────────────────
@api_bp.route('/auth/pin-login', methods=['POST'])
@csrf.exempt
def pin_login():
    data = request.get_json(silent=True) or {}
    pin = data.get('pin', '')
    if pin != ACCESS_PIN:
        return jsonify({'error': 'Invalid PIN'}), 401
    token = create_access_token(identity='mobile-user')
    return jsonify({'access_token': token}), 200


# ── Dashboard ─────────────────────────────────────────────────────
@api_bp.route('/dashboard')
@jwt_required()
def dashboard():
    active_runs = TestRun.query.filter(
        TestRun.status.in_(['queued', 'running'])
    ).count()
    open_bugs = Bug.query.filter_by(status='open').count()

    recent_runs = TestRun.query.filter(
        TestRun.status.in_(['passed', 'failed'])
    ).order_by(TestRun.finished_at.desc()).limit(10).all()
    pass_rate = round(
        sum(r.pass_rate for r in recent_runs if r.pass_rate) / len(recent_runs), 1
    ) if recent_runs else 0

    logs = SimulatorLog.query.order_by(
        SimulatorLog.created_at.desc()
    ).limit(10).all()

    return jsonify({
        'active_runs': active_runs,
        'open_bugs': open_bugs,
        'pass_rate_today': pass_rate,
        'recent_logs': [
            {'message': l.message, 'job_type': l.job_type,
             'created_at': l.created_at.isoformat()}
            for l in logs
        ]
    })


# ── Runs ──────────────────────────────────────────────────────────
@api_bp.route('/runs')
@jwt_required()
def runs():
    items = TestRun.query.order_by(TestRun.created_at.desc()).limit(50).all()
    return jsonify([{
        'id': r.id,
        'suite_name': r.suite.name if r.suite else '—',
        'status': r.status,
        'pass_rate': r.pass_rate,
        'pass_count': r.pass_count,
        'fail_count': r.fail_count,
        'total_count': r.total_count,
        'trigger_type': r.trigger_type,
        'branch': r.branch,
        'started_at': r.started_at.isoformat() if r.started_at else None,
        'finished_at': r.finished_at.isoformat() if r.finished_at else None,
    } for r in items])


@api_bp.route('/runs/<run_id>')
@jwt_required()
def run_detail(run_id):
    r = TestRun.query.get_or_404(run_id)
    return jsonify({
        'id': r.id,
        'suite_name': r.suite.name if r.suite else '—',
        'status': r.status,
        'pass_rate': r.pass_rate,
        'pass_count': r.pass_count,
        'fail_count': r.fail_count,
        'skip_count': r.skip_count,
        'total_count': r.total_count,
        'trigger_type': r.trigger_type,
        'branch': r.branch,
        'ci_build_id': r.ci_build_id,
        'ci_pipeline_url': r.ci_pipeline_url,
        'ai_root_cause': r.ai_root_cause,
        'started_at': r.started_at.isoformat() if r.started_at else None,
        'finished_at': r.finished_at.isoformat() if r.finished_at else None,
    })


# ── Bugs ──────────────────────────────────────────────────────────
@api_bp.route('/bugs')
@jwt_required()
def bugs():
    items = Bug.query.order_by(Bug.created_at.desc()).limit(50).all()
    return jsonify([{
        'id': b.id,
        'title': b.title,
        'severity': b.severity,
        'priority': b.priority,
        'status': b.status,
        'assignee': b.assignee.full_name if b.assignee else None,
        'jira_ticket_id': b.jira_ticket_id,
        'created_at': b.created_at.isoformat(),
    } for b in items])


@api_bp.route('/bugs/<bug_id>')
@jwt_required()
def bug_detail(bug_id):
    b = Bug.query.get_or_404(bug_id)
    return jsonify({
        'id': b.id,
        'title': b.title,
        'description': b.description,
        'severity': b.severity,
        'priority': b.priority,
        'status': b.status,
        'assignee': b.assignee.full_name if b.assignee else None,
        'reporter': b.reporter.full_name if b.reporter else None,
        'jira_ticket_id': b.jira_ticket_id,
        'jira_ticket_url': b.jira_ticket_url,
        'ai_summary': b.ai_summary,
        'ai_root_cause': b.ai_root_cause,
        'labels': b.labels,
        'created_at': b.created_at.isoformat(),
    })


# ── Initiatives ───────────────────────────────────────────────────
@api_bp.route('/initiatives')
@jwt_required()
def initiatives():
    items = Initiative.query.order_by(Initiative.created_at.desc()).all()
    return jsonify([{
        'id': i.id,
        'name': i.name,
        'description': i.description,
        'status': i.status,
        'coverage_pct': i.coverage_pct,
        'target_date': i.target_date.isoformat() if i.target_date else None,
        'owner': i.owner.full_name if i.owner else None,
        'jira_epic_key': i.jira_epic_key,
    } for i in items])


# ── Analytics ─────────────────────────────────────────────────────
@api_bp.route('/analytics/summary')
@jwt_required()
def analytics_summary():
    from datetime import datetime, timedelta
    since = datetime.utcnow() - timedelta(days=7)

    runs_7d = TestRun.query.filter(
        TestRun.created_at >= since,
        TestRun.status.in_(['passed', 'failed'])
    ).all()
    avg_pass_rate = round(
        sum(r.pass_rate for r in runs_7d if r.pass_rate) / len(runs_7d), 1
    ) if runs_7d else 0

    bugs_opened = Bug.query.filter(Bug.created_at >= since).count()
    bugs_resolved = Bug.query.filter(
        Bug.created_at >= since,
        Bug.status == 'resolved'
    ).count()

    return jsonify({
        'pass_rate_7d': avg_pass_rate,
        'total_runs_7d': len(runs_7d),
        'bugs_opened_7d': bugs_opened,
        'bugs_resolved_7d': bugs_resolved,
    })


# ── Integrations ──────────────────────────────────────────────────
@api_bp.route('/integrations')
@jwt_required()
def integrations():
    items = Integration.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': i.id,
        'name': i.name,
        'type': i.type,
        'health_status': i.health_status,
        'last_health_check': i.last_health_check.isoformat() if i.last_health_check else None,
    } for i in items])

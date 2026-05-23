from datetime import datetime, timedelta, timezone
from flask_login import current_user
from app.models.test_run import TestRun
from app.models.bug import Bug
from app.models.test_plan import Initiative, Release
from app.models.retro import SprintRetro, RetroActionItem
from app.models.allocation import Allocation
from app.models.integration import Integration
from app.models.notification import Notification


def get_dashboard_summary(org_id: str) -> dict:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)

    # --- Execution Hub ---
    runs_today = TestRun.query.filter(
        TestRun.org_id == org_id,
        TestRun.created_at >= today_start,
        TestRun.is_deleted == False
    ).all()

    recent_runs = TestRun.query.filter_by(org_id=org_id, is_deleted=False)\
        .order_by(TestRun.created_at.desc()).limit(3).all()

    week_runs = TestRun.query.filter(
        TestRun.org_id == org_id,
        TestRun.created_at >= week_ago,
        TestRun.is_deleted == False,
        TestRun.status.in_(['passed', 'failed', 'partial'])
    ).all()
    total_7d = sum(r.total_count for r in week_runs)
    passed_7d = sum(r.pass_count for r in week_runs)
    pass_rate_7d = round(passed_7d / total_7d * 100, 1) if total_7d > 0 else 0.0

    open_bugs = Bug.query.filter_by(org_id=org_id, is_deleted=False, status='open').count()
    blocker_bugs = Bug.query.filter_by(org_id=org_id, is_deleted=False, status='open', severity='blocker').count()
    critical_bugs = Bug.query.filter_by(org_id=org_id, is_deleted=False, status='open', severity='critical').count()
    recent_bugs = Bug.query.filter_by(org_id=org_id, is_deleted=False)\
        .order_by(Bug.created_at.desc()).limit(3).all()

    # --- Action Center ---
    my_items_count = 0
    if current_user.is_authenticated:
        my_items_count = Bug.query.filter_by(
            org_id=org_id, assigned_to=current_user.id,
            status='open', is_deleted=False
        ).count()

    current_retro = SprintRetro.query.filter_by(org_id=org_id, status='open', is_deleted=False)\
        .order_by(SprintRetro.created_at.desc()).first()
    retro_actions_open = current_retro.open_action_count if current_retro else 0

    unallocated = Allocation.query.filter_by(org_id=org_id, owner_id=None, is_deleted=False).count()

    # --- Automation & Tools ---
    integrations = Integration.query.filter_by(org_id=org_id, is_deleted=False).all()
    tools_healthy = sum(1 for i in integrations if i.health_status == 'healthy')

    # --- Planning & Release ---
    active_initiatives = Initiative.query.filter_by(org_id=org_id, status='active', is_deleted=False).limit(3).all()
    upcoming_releases = Release.query.filter(
        Release.org_id == org_id,
        Release.status.in_(['planning', 'in_progress']),
        Release.is_deleted == False
    ).order_by(Release.target_date.asc()).limit(3).all()

    # --- Notifications ---
    unread_notifications = 0
    if current_user.is_authenticated:
        unread_notifications = Notification.query.filter_by(
            user_id=current_user.id, is_read=False, is_deleted=False
        ).count()

    return {
        'execution': {
            'runs_today': len(runs_today),
            'running': sum(1 for r in runs_today if r.status == 'running'),
            'pass_rate_7d': pass_rate_7d,
            'recent_runs': recent_runs,
            'open_bugs': open_bugs,
            'blocker_bugs': blocker_bugs,
            'critical_bugs': critical_bugs,
            'recent_bugs': recent_bugs,
        },
        'action_center': {
            'my_items': my_items_count,
            'retro': current_retro,
            'retro_actions_open': retro_actions_open,
            'unallocated': unallocated,
            'unread_notifications': unread_notifications,
        },
        'analytics': {
            'pass_rate_7d': pass_rate_7d,
            'total_runs_7d': len(week_runs),
        },
        'automation': {
            'integrations': integrations,
            'tools_count': len(integrations),
            'tools_healthy': tools_healthy,
        },
        'planning': {
            'active_initiatives': active_initiatives,
            'upcoming_releases': upcoming_releases,
            'pending_signoffs': Release.query.filter_by(
                org_id=org_id, status='in_progress', sign_off_by=None, is_deleted=False
            ).count(),
        },
    }

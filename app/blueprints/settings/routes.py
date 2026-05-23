import logging
from flask import render_template, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.blueprints.settings import settings_bp
from app.models.simulator import SimulatorConfig, SimulatorLog
from app.extensions import db

logger = logging.getLogger(__name__)

JOB_MAP = {
    'write_test_case': ('sim_write_test_case', 'Write test cases', '45s'),
    'start_run':       ('sim_start_run',        'Start test runs',         '2 min'),
    'complete_run':    ('sim_complete_run',      'Complete running runs',   '60s'),
    'file_bug':        ('sim_file_bug',          'File bugs',               '90s'),
    'automation_run':  ('sim_automation_run',    'Automation runs',         '3 min'),
}


def _get_or_create_config(org_id):
    config = SimulatorConfig.query.filter_by(org_id=org_id).first()
    if not config:
        config = SimulatorConfig(org_id=org_id)
        db.session.add(config)
        db.session.commit()
    return config


@settings_bp.route('/simulator')
@login_required
def simulator():
    # Role restriction removed from GET — all authenticated users can view simulator settings
    config = _get_or_create_config(current_user.org_id)
    logs = (SimulatorLog.query
            .filter_by(org_id=current_user.org_id)
            .order_by(SimulatorLog.created_at.desc())
            .limit(30)
            .all())
    return render_template('settings/simulator.html', config=config, logs=logs, job_map=JOB_MAP)


@settings_bp.route('/simulator/toggle', methods=['POST'])
@login_required
def toggle_simulator():
    if current_user.role not in ('admin', 'qa_manager'):
        return jsonify({'error': 'Forbidden'}), 403
    config = _get_or_create_config(current_user.org_id)
    config.enabled = not config.enabled
    db.session.commit()

    if config.enabled:
        if not config.seeded:
            try:
                from flask import current_app
                from app.simulator.seeder import run_seed
                run_seed(current_app._get_current_object(), current_user.org_id)
            except Exception:
                logger.exception('Seeder failed on enable')
        _apply_job_states(config)
    else:
        _pause_all_jobs()

    return jsonify({'enabled': config.enabled})


@settings_bp.route('/simulator/job/<job_key>', methods=['POST'])
@login_required
def toggle_job(job_key):
    if current_user.role not in ('admin', 'qa_manager'):
        return jsonify({'error': 'Forbidden'}), 403
    if job_key not in JOB_MAP:
        return jsonify({'error': 'Unknown job'}), 404
    config = _get_or_create_config(current_user.org_id)

    attr = f'job_{job_key}'
    new_val = not getattr(config, attr, True)
    setattr(config, attr, new_val)
    db.session.commit()

    job_id = JOB_MAP[job_key][0]
    try:
        from app.simulator.engine import resume_job, pause_job
        if config.enabled and new_val:
            resume_job(job_id)
        else:
            pause_job(job_id)
    except Exception:
        pass

    return jsonify({'enabled': new_val})


@settings_bp.route('/simulator/log')
@login_required
def simulator_log():
    logs = (SimulatorLog.query
            .filter_by(org_id=current_user.org_id)
            .order_by(SimulatorLog.created_at.desc())
            .limit(30)
            .all())
    return jsonify([
        {'time': l.created_at.strftime('%H:%M:%S'), 'job_type': l.job_type, 'message': l.message}
        for l in logs
    ])


def _apply_job_states(config):
    try:
        from app.simulator.engine import resume_job, pause_job
        flags = {
            'sim_write_test_case': config.job_write_test_case,
            'sim_start_run':       config.job_start_run,
            'sim_complete_run':    config.job_complete_run,
            'sim_file_bug':        config.job_file_bug,
            'sim_automation_run':  config.job_automation_run,
        }
        for job_id, enabled in flags.items():
            if enabled:
                resume_job(job_id)
            else:
                pause_job(job_id)
    except Exception:
        pass


def _pause_all_jobs():
    try:
        from app.simulator.engine import pause_job
        for job_id in JOB_MAP.values():
            pause_job(job_id[0])
    except Exception:
        pass

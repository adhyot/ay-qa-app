import logging
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

JOB_DEFS = [
    ('sim_write_test_case', 45),
    ('sim_start_run', 120),
    ('sim_complete_run', 60),
    ('sim_file_bug', 90),
    ('sim_automation_run', 180),
]

JOB_CONFIG_ATTRS = {
    'sim_write_test_case': 'job_write_test_case',
    'sim_start_run': 'job_start_run',
    'sim_complete_run': 'job_complete_run',
    'sim_file_bug': 'job_file_bug',
    'sim_automation_run': 'job_automation_run',
}


def start_scheduler(app):
    if app.config.get('TESTING'):
        return

    from app.simulator import jobs

    job_funcs = {
        'sim_write_test_case': jobs.job_write_test_case,
        'sim_start_run': jobs.job_start_run,
        'sim_complete_run': jobs.job_complete_run,
        'sim_file_bug': jobs.job_file_bug,
        'sim_automation_run': jobs.job_automation_run,
    }

    for job_id, seconds in JOB_DEFS:
        scheduler.add_job(
            job_funcs[job_id],
            'interval',
            seconds=seconds,
            id=job_id,
            max_instances=1,
            next_run_time=None,
            args=[app],
        )

    scheduler.start()
    logger.info("Simulator scheduler started (all jobs paused)")

    _restore_state(app)


def _restore_state(app):
    with app.app_context():
        try:
            from app.models.simulator import SimulatorConfig
            configs = SimulatorConfig.query.filter_by(enabled=True).all()
            for config in configs:
                _apply_config(config)
            if configs:
                logger.info(f"Restored simulator state for {len(configs)} org(s)")
        except Exception as e:
            logger.warning(f"Could not restore simulator state: {e}")


def _apply_config(config):
    for job_id, attr in JOB_CONFIG_ATTRS.items():
        if config.enabled and getattr(config, attr, False):
            resume_job(job_id)


def resume_job(job_id):
    job = scheduler.get_job(job_id)
    if job:
        job.resume()
        logger.info(f"Simulator job {job_id} resumed")


def pause_job(job_id):
    job = scheduler.get_job(job_id)
    if job:
        job.pause()
        logger.info(f"Simulator job {job_id} paused")

import random
import logging
from datetime import datetime, timezone
from faker import Faker

logger = logging.getLogger(__name__)
fake = Faker()

_ACTIONS = ['Verify', 'Validate', 'Confirm', 'Ensure', 'Check', 'Test']
_SUBJECTS = [
    'login flow', 'password reset', 'OAuth callback', 'session timeout',
    'checkout form', 'payment gateway', 'order confirmation', 'cart update',
    'API response time', 'rate limiting', 'authentication header', 'error response',
    'mobile navigation', 'responsive layout', 'offline mode', 'push notifications',
]
_CONDITIONS = [
    'with valid credentials', 'when session expires', 'on slow network',
    'with invalid input', 'after 3 failed attempts', 'with 2FA enabled',
    'under high load', 'with empty cart', 'from mobile device',
]
_BUG_TITLES = [
    'Login fails with valid credentials on Safari',
    'Payment gateway timeout after 30s',
    'Cart total not updating after coupon applied',
    'API returns 500 on concurrent requests',
    'Mobile navigation menu not closing on tap',
    'Session expires prematurely on idle',
    'Search results not reflecting applied filters',
    'Email not sent on password reset',
    'Order confirmation missing item details',
    'Rate limiter blocking legitimate requests',
    'Checkout button unresponsive on mobile',
    '2FA code not accepted after clock drift',
]


def _get_config():
    from app.models.simulator import SimulatorConfig
    return SimulatorConfig.query.filter_by(enabled=True).first()


def _get_sim_user(org_id):
    from app.models.user import User
    count = User.query.filter_by(org_id=org_id, is_active=True).filter(
        User.email.like('sim_%')
    ).count()
    if count == 0:
        return User.query.filter_by(org_id=org_id, is_active=True).first()
    user = (User.query
            .filter_by(org_id=org_id, is_active=True)
            .filter(User.email.like('sim_%'))
            .order_by(User.id)
            .offset(random.randint(0, count - 1))
            .first())
    return user


def _append_log(org_id, job_type, message):
    from app.models.simulator import SimulatorLog
    from app.extensions import db
    log = SimulatorLog(org_id=org_id, job_type=job_type, message=message)
    db.session.add(log)


def _trim_log(org_id):
    from app.models.simulator import SimulatorLog
    from app.extensions import db
    count = SimulatorLog.query.filter_by(org_id=org_id).count()
    if count > 200:
        excess = count - 180
        oldest = (SimulatorLog.query
                  .filter_by(org_id=org_id)
                  .order_by(SimulatorLog.created_at.asc())
                  .limit(excess)
                  .with_entities(SimulatorLog.id)
                  .all())
        ids = [r.id for r in oldest]
        SimulatorLog.query.filter(SimulatorLog.id.in_(ids)).delete(synchronize_session=False)


def job_write_test_case(app):
    with app.app_context():
        from app.extensions import db
        from app.models.test_case import TestSuite, TestCase
        try:
            config = _get_config()
            if not config or not config.job_write_test_case:
                return

            suite_count = TestSuite.query.filter_by(org_id=config.org_id, is_deleted=False).count()
            if suite_count == 0:
                return
            suite = (TestSuite.query
                     .filter_by(org_id=config.org_id, is_deleted=False)
                     .order_by(TestSuite.id)
                     .offset(random.randint(0, max(0, suite_count - 1)))
                     .first())
            if not suite:
                return

            creator = _get_sim_user(config.org_id)
            title = f"{random.choice(_ACTIONS)} {random.choice(_SUBJECTS)} {random.choice(_CONDITIONS)}"
            priority = random.choices(['critical', 'high', 'medium', 'low'], weights=[5, 25, 50, 20])[0]
            type_ = random.choices(['manual', 'automated', 'hybrid'], weights=[30, 50, 20])[0]
            steps = [
                {'order': i + 1, 'action': fake.sentence(nb_words=6), 'expected_result': fake.sentence(nb_words=5)}
                for i in range(random.randint(2, 4))
            ]

            tc = TestCase(
                suite_id=suite.id,
                org_id=config.org_id,
                title=title,
                description=fake.sentence(nb_words=10),
                steps=steps,
                priority=priority,
                type=type_,
                created_by=creator.id if creator else None,
                updated_by=creator.id if creator else None,
            )
            db.session.add(tc)

            name = creator.full_name if creator else 'Engineer'
            _append_log(config.org_id, 'write_test_case',
                        f'{name} added "{title}" → {suite.name}')
            db.session.commit()
            _trim_log(config.org_id)
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.exception('job_write_test_case failed')


def job_start_run(app):
    with app.app_context():
        from app.extensions import db
        from app.models.test_case import TestSuite
        from app.models.test_run import TestRun
        try:
            config = _get_config()
            if not config or not config.job_start_run:
                return

            suite_count = TestSuite.query.filter_by(org_id=config.org_id, is_deleted=False).count()
            if suite_count == 0:
                return
            suite = (TestSuite.query
                     .filter_by(org_id=config.org_id, is_deleted=False)
                     .order_by(TestSuite.id)
                     .offset(random.randint(0, max(0, suite_count - 1)))
                     .first())
            if not suite or suite.total_cases == 0:
                return

            triggerer = _get_sim_user(config.org_id)
            trigger_type = random.choices(['manual', 'ci_cd'], weights=[40, 60])[0]

            run = TestRun(
                suite_id=suite.id,
                org_id=config.org_id,
                triggered_by=triggerer.id if triggerer else None,
                trigger_type=trigger_type,
                status='running',
                total_count=suite.total_cases,
                branch='main' if trigger_type == 'ci_cd' else None,
                started_at=datetime.now(timezone.utc),
            )
            db.session.add(run)

            label = 'CI triggered' if trigger_type == 'ci_cd' else (triggerer.full_name if triggerer else 'Engineer')
            _append_log(config.org_id, 'start_run',
                        f'{label} started run on {suite.name} ({suite.total_cases} tests)')
            db.session.commit()
            _trim_log(config.org_id)
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.exception('job_start_run failed')


def job_complete_run(app):
    with app.app_context():
        from app.extensions import db
        from app.models.test_case import TestCase
        from app.models.test_run import TestRun, TestRunResult
        try:
            config = _get_config()
            if not config or not config.job_complete_run:
                return

            run = (TestRun.query
                   .filter(
                       TestRun.org_id == config.org_id,
                       TestRun.status.in_(['queued', 'running']),
                       TestRun.is_deleted == False,
                   )
                   .order_by(TestRun.created_at.asc())
                   .first())
            if not run:
                return

            suite_name = run.suite.name if run.suite else 'suite'
            now = datetime.now(timezone.utc)
            if not run.started_at:
                run.started_at = now

            test_cases = TestCase.query.filter_by(suite_id=run.suite_id, is_deleted=False).all()
            if not test_cases:
                run.status = 'cancelled'
                db.session.commit()
                return

            r = random.random()
            if r < 0.60:
                pass_pct = random.uniform(0.90, 1.00)
            elif r < 0.85:
                pass_pct = random.uniform(0.70, 0.89)
            else:
                pass_pct = random.uniform(0.50, 0.69)

            total = len(test_cases)
            pass_count = round(total * pass_pct)
            fail_count = total - pass_count

            for i, tc in enumerate(test_cases):
                status = 'passed' if i < pass_count else 'failed'
                result = TestRunResult(
                    run_id=run.id,
                    org_id=run.org_id,
                    test_case_id=tc.id,
                    status=status,
                    duration_ms=random.randint(100, 8000),
                    started_at=run.started_at,
                    finished_at=now,
                    error_message=(
                        'AssertionError: expected element to be visible'
                        if status == 'failed' else None
                    ),
                )
                db.session.add(result)

            run.pass_count = pass_count
            run.fail_count = fail_count
            run.total_count = total
            run.finished_at = now
            run.status = 'passed' if fail_count == 0 else ('failed' if pass_count == 0 else 'partial')

            rate = round(pass_count / total * 100, 1)
            _append_log(config.org_id, 'complete_run',
                        f'Run completed: {pass_count}/{total} passed ({rate}%) on {suite_name}')
            db.session.commit()
            _trim_log(config.org_id)
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.exception('job_complete_run failed')


def job_file_bug(app):
    with app.app_context():
        from app.extensions import db
        from app.models.test_run import TestRunResult
        from app.models.bug import Bug
        try:
            config = _get_config()
            if not config or not config.job_file_bug:
                return

            from app.extensions import db as _db
            bugged_ids = _db.session.query(Bug.run_result_id).filter(
                Bug.org_id == config.org_id,
                Bug.run_result_id.isnot(None),
            ).scalar_subquery()

            result = (TestRunResult.query
                      .filter(
                          TestRunResult.org_id == config.org_id,
                          TestRunResult.status == 'failed',
                          ~TestRunResult.id.in_(bugged_ids),
                      )
                      .order_by(TestRunResult.created_at.desc())
                      .first())
            if not result:
                return

            reporter = _get_sim_user(config.org_id)
            assignee = _get_sim_user(config.org_id)
            severity = random.choices(
                ['blocker', 'critical', 'major', 'minor', 'trivial'],
                weights=[5, 20, 35, 30, 10],
            )[0]

            bug = Bug(
                org_id=config.org_id,
                title=random.choice(_BUG_TITLES),
                description=fake.paragraph(nb_sentences=3),
                severity=severity,
                priority=random.choices(['critical', 'high', 'medium', 'low'], weights=[10, 30, 45, 15])[0],
                status='open',
                reported_by=reporter.id if reporter else None,
                assigned_to=assignee.id if assignee else None,
                run_result_id=result.id,
            )
            db.session.add(bug)

            assignee_name = assignee.full_name if assignee else 'Engineer'
            _append_log(config.org_id, 'file_bug',
                        f'Bug filed: {bug.title} – {severity.upper()} → assigned to {assignee_name}')
            db.session.commit()
            _trim_log(config.org_id)
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.exception('job_file_bug failed')


def job_automation_run(app):
    with app.app_context():
        from app.extensions import db
        from app.models.test_case import TestSuite
        from app.models.test_run import TestRun
        try:
            config = _get_config()
            if not config or not config.job_automation_run:
                return

            suite_count = TestSuite.query.filter_by(org_id=config.org_id, is_deleted=False).count()
            if suite_count == 0:
                return
            suite = (TestSuite.query
                     .filter_by(org_id=config.org_id, is_deleted=False)
                     .order_by(TestSuite.id)
                     .offset(random.randint(0, max(0, suite_count - 1)))
                     .first())
            if not suite:
                return

            branch = random.choices(
                ['main', 'develop', f'feature/ACME-{random.randint(100, 999)}'],
                weights=[50, 30, 20],
            )[0]
            build_id = f'build-{random.randint(1000, 9999)}'
            total = suite.total_cases or random.randint(20, 50)

            run = TestRun(
                suite_id=suite.id,
                org_id=config.org_id,
                trigger_type='ci_cd',
                status='queued',
                total_count=total,
                branch=branch,
                ci_build_id=build_id,
                ci_pipeline_url=f'https://github.com/acme/app/actions/runs/{random.randint(10000000, 99999999)}',
            )
            db.session.add(run)

            _append_log(config.org_id, 'automation_run',
                        f'CI automation queued: {build_id} on {branch} → {suite.name} ({total} tests)')
            db.session.commit()
            _trim_log(config.org_id)
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.exception('job_automation_run failed')

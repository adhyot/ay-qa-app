# Demo Simulation Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a background simulation engine embedded in the Flask app that generates realistic QA team activity (test case writing, test runs, bug filing, CI automation) against the demo org, controlled from a Settings page with a master toggle, per-job toggles, and a live activity log.

**Architecture:** APScheduler `BackgroundScheduler` starts with the Flask app (skipped in testing), registers 5 interval jobs in a paused state, then restores their enabled/paused state from `SimulatorConfig` in the DB. A `settings` blueprint at `/settings/simulator` provides master toggle, per-job toggles, and a JSON log endpoint polled every 10s by vanilla JS.

**Tech Stack:** Python/Flask 3.1, APScheduler 3.x, SQLAlchemy/Flask-SQLAlchemy, Faker (already installed), Jinja2, vanilla JS fetch for log polling.

---

## File Map

**New files:**
- `app/models/simulator.py` — `SimulatorConfig` and `SimulatorLog` models
- `app/simulator/__init__.py` — exports `start_scheduler`
- `app/simulator/engine.py` — APScheduler singleton, `start_scheduler`, `resume_job`, `pause_job`
- `app/simulator/jobs.py` — 5 job functions + `_append_log` / `_trim_log` helpers
- `app/simulator/seeder.py` — one-time seed: virtual users, suites, test cases, environments
- `app/blueprints/settings/__init__.py` — `settings_bp` Blueprint
- `app/blueprints/settings/routes.py` — simulator control routes
- `app/templates/settings/simulator.html` — settings UI
- `tests/test_simulator_models.py` — model unit tests
- `tests/test_simulator_jobs.py` — job function unit tests
- `tests/test_settings_routes.py` — settings route tests

**Modified files:**
- `requirements.txt` — add `APScheduler>=3.10`
- `app/models/__init__.py` — import `SimulatorConfig`, `SimulatorLog`
- `app/__init__.py` — call `start_scheduler(app)`, register `settings_bp`
- `app/templates/base.html` — add Settings link to grid nav dropdown

---

## Task 1: Install APScheduler

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add APScheduler to requirements.txt**

Open `requirements.txt` and add this line after the existing entries:
```
APScheduler>=3.10,<4.0
```

- [ ] **Step 2: Install it**

```bash
cd /Users/adhyot/PycharmProjects/ay-qa-app && .venv/bin/pip install "APScheduler>=3.10,<4.0"
```

Expected: `Successfully installed APScheduler-3.x.x`

- [ ] **Step 3: Verify import works**

```bash
.venv/bin/python -c "from apscheduler.schedulers.background import BackgroundScheduler; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "feat: add APScheduler dependency for demo simulation engine"
```

---

## Task 2: Create SimulatorConfig and SimulatorLog Models

**Files:**
- Create: `app/models/simulator.py`
- Modify: `app/models/__init__.py`
- Create: `tests/test_simulator_models.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_simulator_models.py`:

```python
import pytest
from app.models.simulator import SimulatorConfig, SimulatorLog
from app.extensions import db as _db


@pytest.fixture
def org_id(app):
    with app.app_context():
        from app.models.organization import Organization
        org = Organization.query.first()
        return org.id


def test_simulator_config_defaults(app, org_id):
    with app.app_context():
        config = SimulatorConfig(org_id=org_id)
        _db.session.add(config)
        _db.session.commit()

        fetched = SimulatorConfig.query.filter_by(org_id=org_id).first()
        assert fetched is not None
        assert fetched.enabled is False
        assert fetched.seeded is False
        assert fetched.job_write_test_case is True
        assert fetched.job_start_run is True
        assert fetched.job_complete_run is True
        assert fetched.job_file_bug is True
        assert fetched.job_automation_run is True

        _db.session.delete(fetched)
        _db.session.commit()


def test_simulator_log_create(app, org_id):
    with app.app_context():
        log = SimulatorLog(org_id=org_id, job_type='write_test_case', message='Test message')
        _db.session.add(log)
        _db.session.commit()

        fetched = SimulatorLog.query.filter_by(org_id=org_id).first()
        assert fetched.job_type == 'write_test_case'
        assert fetched.message == 'Test message'
        assert fetched.created_at is not None

        _db.session.delete(fetched)
        _db.session.commit()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
.venv/bin/pytest tests/test_simulator_models.py -v 2>&1 | head -20
```

Expected: `ImportError` — `SimulatorConfig` not found.

- [ ] **Step 3: Create the models**

Create `app/models/simulator.py`:

```python
from datetime import datetime, timezone
from app.extensions import db
from app.models.base import generate_uuid


class SimulatorConfig(db.Model):
    __tablename__ = 'simulator_configs'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    org_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False, unique=True)
    enabled = db.Column(db.Boolean, default=False, nullable=False)
    seeded = db.Column(db.Boolean, default=False, nullable=False)
    job_write_test_case = db.Column(db.Boolean, default=True, nullable=False)
    job_start_run = db.Column(db.Boolean, default=True, nullable=False)
    job_complete_run = db.Column(db.Boolean, default=True, nullable=False)
    job_file_bug = db.Column(db.Boolean, default=True, nullable=False)
    job_automation_run = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SimulatorLog(db.Model):
    __tablename__ = 'simulator_logs'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    org_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False, index=True)
    job_type = db.Column(db.String(30), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
```

- [ ] **Step 4: Add imports to `app/models/__init__.py`**

Append to the end of `app/models/__init__.py`:

```python
from app.models.simulator import SimulatorConfig, SimulatorLog
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
.venv/bin/pytest tests/test_simulator_models.py -v
```

Expected: Both tests `PASS` (SQLite in-memory auto-creates the new tables via `create_all` in conftest).

- [ ] **Step 6: Commit**

```bash
git add app/models/simulator.py app/models/__init__.py tests/test_simulator_models.py
git commit -m "feat: add SimulatorConfig and SimulatorLog models"
```

---

## Task 3: Create Alembic Migration

**Files:**
- Auto-generated: `migrations/versions/<hash>_add_simulator_tables.py`

- [ ] **Step 1: Generate the migration**

```bash
.venv/bin/flask db migrate -m "add simulator tables"
```

Expected: `Generating .../migrations/versions/xxxx_add_simulator_tables.py ... done`

- [ ] **Step 2: Inspect the generated migration**

```bash
cat migrations/versions/*add_simulator_tables.py
```

Confirm it contains `op.create_table('simulator_configs', ...)` and `op.create_table('simulator_logs', ...)` in `upgrade()`, and both `op.drop_table(...)` calls in `downgrade()`.

- [ ] **Step 3: Apply the migration**

```bash
.venv/bin/flask db upgrade
```

Expected: `Running upgrade ... -> xxxx` with no errors.

- [ ] **Step 4: Commit**

```bash
git add migrations/
git commit -m "feat: migration for simulator_configs and simulator_logs tables"
```

---

## Task 4: Create the Simulator Engine

**Files:**
- Create: `app/simulator/__init__.py`
- Create: `app/simulator/engine.py`

- [ ] **Step 1: Create `app/simulator/__init__.py`**

```python
from app.simulator.engine import start_scheduler

__all__ = ['start_scheduler']
```

- [ ] **Step 2: Create `app/simulator/engine.py`**

```python
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
```

- [ ] **Step 3: Verify the module imports cleanly**

```bash
.venv/bin/python -c "from app.simulator.engine import scheduler, start_scheduler, resume_job, pause_job; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add app/simulator/__init__.py app/simulator/engine.py
git commit -m "feat: add simulator APScheduler engine"
```

---

## Task 5: Create the 5 Simulator Jobs

**Files:**
- Create: `app/simulator/jobs.py`
- Create: `tests/test_simulator_jobs.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_simulator_jobs.py`:

```python
import pytest
from app.extensions import db as _db
from app.models.organization import Organization
from app.models.user import User
from app.models.test_case import TestSuite, TestCase
from app.models.test_run import TestRun, TestRunResult
from app.models.bug import Bug
from app.models.simulator import SimulatorConfig, SimulatorLog


@pytest.fixture
def sim_setup(app):
    """Creates org, config, suite, test cases, and a virtual user for job tests."""
    with app.app_context():
        org = Organization.query.first()

        config = SimulatorConfig(org_id=org.id, enabled=True,
                                  job_write_test_case=True, job_start_run=True,
                                  job_complete_run=True, job_file_bug=True,
                                  job_automation_run=True)
        _db.session.add(config)

        user = User(org_id=org.id, email='sim_tester@simcorp.qa',
                    full_name='Sim Tester', role='qa_engineer')
        user.set_password('test1234')
        _db.session.add(user)

        suite = TestSuite(org_id=org.id, name='Test Suite Alpha',
                          framework='pytest', github_repo='acme/alpha')
        _db.session.add(suite)
        _db.session.flush()

        for i in range(5):
            tc = TestCase(org_id=org.id, suite_id=suite.id,
                          title=f'Test case {i}', priority='medium', type='automated')
            _db.session.add(tc)

        _db.session.commit()

        yield {'org_id': org.id, 'suite_id': suite.id, 'user_id': user.id}

        SimulatorLog.query.filter_by(org_id=org.id).delete()
        TestRunResult.query.filter(
            TestRunResult.run_id.in_(
                _db.session.query(TestRun.id).filter_by(org_id=org.id)
            )
        ).delete(synchronize_session=False)
        Bug.query.filter_by(org_id=org.id).delete()
        TestRun.query.filter_by(org_id=org.id).delete()
        TestCase.query.filter_by(org_id=org.id, suite_id=suite.id).delete()
        _db.session.delete(suite)
        SimulatorConfig.query.filter_by(org_id=org.id).delete()
        _db.session.delete(user)
        _db.session.commit()


def test_job_write_test_case(app, sim_setup):
    from app.simulator.jobs import job_write_test_case
    with app.app_context():
        org_id = sim_setup['org_id']
        before = TestCase.query.filter_by(org_id=org_id).count()
        job_write_test_case(app)
        after = TestCase.query.filter_by(org_id=org_id).count()
        assert after == before + 1
        log = SimulatorLog.query.filter_by(org_id=org_id, job_type='write_test_case').first()
        assert log is not None


def test_job_start_run(app, sim_setup):
    from app.simulator.jobs import job_start_run
    with app.app_context():
        org_id = sim_setup['org_id']
        before = TestRun.query.filter_by(org_id=org_id).count()
        job_start_run(app)
        after = TestRun.query.filter_by(org_id=org_id).count()
        assert after == before + 1
        run = TestRun.query.filter_by(org_id=org_id).first()
        assert run.status == 'running'


def test_job_complete_run(app, sim_setup):
    from app.simulator.jobs import job_start_run, job_complete_run
    with app.app_context():
        org_id = sim_setup['org_id']
        job_start_run(app)
        job_complete_run(app)
        run = TestRun.query.filter_by(org_id=org_id).first()
        assert run.status in ('passed', 'failed', 'partial')
        assert run.total_count > 0
        assert TestRunResult.query.filter_by(run_id=run.id).count() > 0


def test_job_file_bug(app, sim_setup):
    from app.simulator.jobs import job_start_run, job_complete_run, job_file_bug
    with app.app_context():
        org_id = sim_setup['org_id']
        job_start_run(app)
        job_complete_run(app)
        run = TestRun.query.filter_by(org_id=org_id).first()
        if run.fail_count == 0:
            result = TestRunResult.query.filter_by(run_id=run.id).first()
            result.status = 'failed'
            _db.session.commit()
        before = Bug.query.filter_by(org_id=org_id).count()
        job_file_bug(app)
        after = Bug.query.filter_by(org_id=org_id).count()
        assert after == before + 1


def test_job_automation_run(app, sim_setup):
    from app.simulator.jobs import job_automation_run
    with app.app_context():
        org_id = sim_setup['org_id']
        before = TestRun.query.filter_by(org_id=org_id).count()
        job_automation_run(app)
        after = TestRun.query.filter_by(org_id=org_id).count()
        assert after == before + 1
        run = TestRun.query.filter_by(org_id=org_id).order_by(TestRun.created_at.desc()).first()
        assert run.trigger_type == 'ci_cd'
        assert run.status == 'queued'


def test_job_skips_when_disabled(app, sim_setup):
    from app.simulator.jobs import job_write_test_case
    with app.app_context():
        org_id = sim_setup['org_id']
        config = SimulatorConfig.query.filter_by(org_id=org_id).first()
        config.job_write_test_case = False
        _db.session.commit()

        before = TestCase.query.filter_by(org_id=org_id).count()
        job_write_test_case(app)
        after = TestCase.query.filter_by(org_id=org_id).count()
        assert after == before

        config.job_write_test_case = True
        _db.session.commit()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
.venv/bin/pytest tests/test_simulator_jobs.py -v 2>&1 | head -20
```

Expected: `ImportError` — `job_write_test_case` not found.

- [ ] **Step 3: Create `app/simulator/jobs.py`**

```python
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


def _get_config(org_id_hint=None):
    from app.models.simulator import SimulatorConfig
    if org_id_hint:
        return SimulatorConfig.query.filter_by(org_id=org_id_hint, enabled=True).first()
    return SimulatorConfig.query.filter_by(enabled=True).first()


def _get_sim_user(org_id):
    from app.models.user import User
    user = (User.query
            .filter_by(org_id=org_id, is_active=True)
            .filter(User.email.like('sim_%'))
            .order_by(User.id)
            .offset(random.randint(0, 4))
            .first())
    if not user:
        user = User.query.filter_by(org_id=org_id, is_active=True).first()
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

            suite = (TestSuite.query
                     .filter_by(org_id=config.org_id, is_deleted=False)
                     .order_by(TestSuite.id)
                     .offset(random.randint(0, 3))
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

            suite = (TestSuite.query
                     .filter_by(org_id=config.org_id, is_deleted=False)
                     .order_by(TestSuite.id)
                     .offset(random.randint(0, 3))
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
                        f'Run completed: {pass_count}/{total} passed ({rate}%) on {run.suite.name if run.suite else "suite"}')
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

            existing_result_ids = [
                b.run_result_id for b in
                Bug.query.filter_by(org_id=config.org_id).filter(Bug.run_result_id.isnot(None)).all()
            ]

            result_q = (TestRunResult.query
                        .filter(
                            TestRunResult.org_id == config.org_id,
                            TestRunResult.status == 'failed',
                        ))
            if existing_result_ids:
                result_q = result_q.filter(~TestRunResult.id.in_(existing_result_ids))
            result = result_q.order_by(TestRunResult.created_at.desc()).first()
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

            suite = (TestSuite.query
                     .filter_by(org_id=config.org_id, is_deleted=False)
                     .order_by(TestSuite.id)
                     .offset(random.randint(0, 3))
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
```

- [ ] **Step 4: Run tests**

```bash
.venv/bin/pytest tests/test_simulator_jobs.py -v
```

Expected: All 6 tests `PASS`.

- [ ] **Step 5: Commit**

```bash
git add app/simulator/jobs.py tests/test_simulator_jobs.py
git commit -m "feat: add 5 simulator job functions with tests"
```

---

## Task 6: Create the Seeder

**Files:**
- Create: `app/simulator/seeder.py`

- [ ] **Step 1: Create `app/simulator/seeder.py`**

```python
import random
import logging
from faker import Faker

logger = logging.getLogger(__name__)
fake = Faker()

_SUITE_CONFIGS = [
    ('Login & Auth', 'pytest', 'acme/auth-service', [
        'Verify login with valid credentials',
        'Validate login fails with wrong password',
        'Confirm password reset email is sent',
        'Ensure 2FA challenge appears when enabled',
        'Check session expires after idle timeout',
        'Verify OAuth callback redirects correctly',
        'Test account lockout after 5 failed attempts',
        'Validate remember-me token persists across sessions',
    ]),
    ('Checkout & Payments', 'selenium', 'acme/checkout', [
        'Verify cart total updates on item quantity change',
        'Validate coupon code applies correct discount',
        'Confirm order confirmation email is sent',
        'Ensure payment gateway handles timeout gracefully',
        'Check checkout completes with saved card',
        'Verify address validation rejects invalid postcode',
        'Test order cancellation within 5 minutes',
        'Validate VAT is calculated correctly for EU orders',
    ]),
    ('API Integration', 'pytest', 'acme/api-gateway', [
        'Verify /health endpoint returns 200',
        'Validate authentication header is required',
        'Confirm rate limiter returns 429 after threshold',
        'Ensure pagination works for large result sets',
        'Check error response format matches schema',
        'Verify idempotency key prevents duplicate orders',
        'Test webhook retry on non-2xx response',
        'Validate JWT expiry returns 401',
    ]),
    ('Mobile Regression', 'playwright', 'acme/mobile-app', [
        'Verify navigation menu opens and closes correctly',
        'Validate bottom tab bar highlights active tab',
        'Confirm pull-to-refresh loads new data',
        'Ensure offline mode shows cached content',
        'Check push notification opens correct screen',
        'Verify responsive layout on 320px viewport',
        'Test deep link opens correct page',
        'Validate swipe gesture on list items',
    ]),
]

_USER_CONFIGS = [
    ('qa_engineer', 'QA Engineer'),
    ('qa_engineer', 'QA Engineer'),
    ('qa_manager', 'QA Manager'),
    ('qa_engineer', 'Automation Engineer'),
    ('viewer', 'Viewer'),
]


def run_seed(app, org_id):
    with app.app_context():
        from app.extensions import db
        from app.models.user import User
        from app.models.test_case import TestSuite, TestCase
        from app.models.environment import Environment
        from app.models.simulator import SimulatorConfig

        try:
            sim_users = _seed_users(db, User, org_id)
            db.session.flush()

            suites = _seed_suites(db, TestSuite, org_id, sim_users)
            db.session.flush()

            _seed_test_cases(db, TestCase, org_id, suites, sim_users)
            _seed_environments(db, Environment, org_id)

            config = SimulatorConfig.query.filter_by(org_id=org_id).first()
            if config:
                config.seeded = True

            db.session.commit()
            logger.info(f'Simulator seed complete for org {org_id}')
        except Exception:
            db.session.rollback()
            logger.exception('Seeder failed')
            raise


def _seed_users(db, User, org_id):
    users = []
    for role, _ in _USER_CONFIGS:
        name = fake.name()
        username = fake.user_name().replace('.', '_')[:12]
        email = f'sim_{username}@simcorp.qa'
        existing = User.query.filter_by(email=email).first()
        if existing:
            users.append(existing)
            continue
        user = User(org_id=org_id, email=email, full_name=name, role=role, is_active=True)
        user.set_password(f'sim_user_{random.randint(1000, 9999)}')
        db.session.add(user)
        users.append(user)
    return users


def _seed_suites(db, TestSuite, org_id, sim_users):
    qa_users = [u for u in sim_users if u.role in ('qa_engineer', 'qa_manager')]
    suites = []
    for name, framework, repo, _ in _SUITE_CONFIGS:
        existing = TestSuite.query.filter_by(org_id=org_id, name=name, is_deleted=False).first()
        if existing:
            suites.append(existing)
            continue
        owner = random.choice(qa_users) if qa_users else None
        suite = TestSuite(
            org_id=org_id,
            name=name,
            description=fake.sentence(nb_words=8),
            framework=framework,
            github_repo=repo,
            owner_id=owner.id if owner else None,
            tags=[framework, 'regression'],
        )
        db.session.add(suite)
        suites.append(suite)
    return suites


def _seed_test_cases(db, TestCase, org_id, suites, sim_users):
    for suite, (_, _, _, titles) in zip(suites, _SUITE_CONFIGS):
        existing_count = TestCase.query.filter_by(suite_id=suite.id, is_deleted=False).count()
        for title in titles[existing_count:]:
            creator = random.choice(sim_users) if sim_users else None
            tc = TestCase(
                suite_id=suite.id,
                org_id=org_id,
                title=title,
                description=fake.sentence(nb_words=10),
                priority=random.choices(['critical', 'high', 'medium', 'low'], weights=[10, 25, 50, 15])[0],
                type=random.choices(['manual', 'automated', 'hybrid'], weights=[25, 55, 20])[0],
                steps=[
                    {
                        'order': i + 1,
                        'action': fake.sentence(nb_words=5),
                        'expected_result': fake.sentence(nb_words=4),
                    }
                    for i in range(random.randint(2, 4))
                ],
                created_by=creator.id if creator else None,
                updated_by=creator.id if creator else None,
            )
            db.session.add(tc)


def _seed_environments(db, Environment, org_id):
    count = Environment.query.filter_by(org_id=org_id, is_deleted=False).count()
    if count > 0:
        return
    for name, env_type, url in [
        ('Staging', 'staging', 'https://staging.acmecorp.io'),
        ('Production', 'production', 'https://app.acmecorp.io'),
    ]:
        env = Environment(
            org_id=org_id,
            name=name,
            type=env_type,
            base_url=url,
            health_status='healthy',
        )
        db.session.add(env)
```

- [ ] **Step 2: Verify the seeder imports cleanly**

```bash
.venv/bin/python -c "from app.simulator.seeder import run_seed; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add app/simulator/seeder.py
git commit -m "feat: add simulator seeder (virtual users, suites, test cases, environments)"
```

---

## Task 7: Create Settings Blueprint and Routes

**Files:**
- Create: `app/blueprints/settings/__init__.py`
- Create: `app/blueprints/settings/routes.py`
- Create: `tests/test_settings_routes.py`

- [ ] **Step 1: Write failing route tests**

Create `tests/test_settings_routes.py`:

```python
import pytest
from app.models.simulator import SimulatorConfig
from app.extensions import db as _db


@pytest.fixture(autouse=True)
def cleanup_config(app):
    yield
    with app.app_context():
        from app.models.organization import Organization
        org = Organization.query.first()
        SimulatorConfig.query.filter_by(org_id=org.id).delete()
        _db.session.commit()


def test_simulator_page_loads(client, app):
    with app.app_context():
        response = client.get('/settings/simulator', follow_redirects=True)
        assert response.status_code == 200
        assert b'Demo Simulation' in response.data


def test_toggle_enables_simulator(client, app):
    with app.app_context():
        from app.models.organization import Organization
        org = Organization.query.first()

        response = client.post('/settings/simulator/toggle',
                               content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data['enabled'] is True

        config = SimulatorConfig.query.filter_by(org_id=org.id).first()
        assert config.enabled is True


def test_toggle_disables_simulator(client, app):
    with app.app_context():
        from app.models.organization import Organization
        org = Organization.query.first()

        config = SimulatorConfig(org_id=org.id, enabled=True, seeded=True)
        _db.session.add(config)
        _db.session.commit()

        response = client.post('/settings/simulator/toggle',
                               content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data['enabled'] is False


def test_toggle_job(client, app):
    with app.app_context():
        from app.models.organization import Organization
        org = Organization.query.first()

        config = SimulatorConfig(org_id=org.id, enabled=True, seeded=True)
        _db.session.add(config)
        _db.session.commit()

        response = client.post('/settings/simulator/job/write_test_case',
                               content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data['enabled'] is False


def test_log_endpoint_returns_json(client, app):
    with app.app_context():
        from app.models.organization import Organization
        from app.models.simulator import SimulatorLog
        org = Organization.query.first()

        log = SimulatorLog(org_id=org.id, job_type='test', message='hello')
        _db.session.add(log)
        _db.session.commit()

        response = client.get('/settings/simulator/log')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert any(entry['message'] == 'hello' for entry in data)

        SimulatorLog.query.filter_by(org_id=org.id).delete()
        _db.session.commit()
```

- [ ] **Step 2: Run to confirm failure**

```bash
.venv/bin/pytest tests/test_settings_routes.py -v 2>&1 | head -20
```

Expected: `404` errors — route not registered yet.

- [ ] **Step 3: Create `app/blueprints/settings/__init__.py`**

```python
from flask import Blueprint

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')
```

- [ ] **Step 4: Create `app/blueprints/settings/routes.py`**

```python
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
    if current_user.role not in ('admin', 'qa_manager'):
        return redirect(url_for('core.dashboard'))
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
```

- [ ] **Step 5: Run the route tests**

```bash
.venv/bin/pytest tests/test_settings_routes.py -v
```

Expected: All 5 tests fail with `404` — blueprint not registered yet (Task 9 wires it in).

- [ ] **Step 6: Commit**

```bash
git add app/blueprints/settings/__init__.py app/blueprints/settings/routes.py tests/test_settings_routes.py
git commit -m "feat: add settings blueprint with simulator control routes"
```

---

## Task 8: Create the Settings Template

**Files:**
- Create: `app/templates/settings/simulator.html`

- [ ] **Step 1: Create the template directory and file**

```bash
mkdir -p /Users/adhyot/PycharmProjects/ay-qa-app/app/templates/settings
```

Create `app/templates/settings/simulator.html`:

```html
{% extends "base.html" %}
{% block title %}Simulator Settings — QA Platform{% endblock %}
{% block page_title %}Settings{% endblock %}

{% block content %}
<div class="module-card" style="max-width:860px;">

  <!-- Header row -->
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;">
    <div>
      <h2 style="font-size:16px;font-weight:700;margin:0 0 4px;">Demo Simulation</h2>
      <p style="font-size:12px;color:var(--color-text-muted);margin:0;">
        Generates realistic QA team activity in the background so the app always has live data.
      </p>
    </div>
    <button
      id="masterToggle"
      data-enabled="{{ 'true' if config.enabled else 'false' }}"
      onclick="toggleMaster()"
      class="btn {% if config.enabled %}btn-primary{% else %}btn-secondary{% endif %}"
      style="min-width:100px;">
      {% if config.enabled %}● Enabled{% else %}○ Disabled{% endif %}
    </button>
  </div>

  <!-- Jobs table -->
  <div style="margin-bottom:28px;">
    <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--color-text-muted);margin-bottom:10px;">
      Jobs
    </div>
    <table style="width:100%;border-collapse:collapse;font-size:13px;">
      <thead>
        <tr style="border-bottom:2px solid var(--color-surface-subtle);">
          <th style="text-align:left;padding:8px 10px;color:var(--color-text-muted);font-size:11px;text-transform:uppercase;letter-spacing:.06em;">Activity</th>
          <th style="text-align:left;padding:8px 10px;color:var(--color-text-muted);font-size:11px;text-transform:uppercase;letter-spacing:.06em;">Interval</th>
          <th style="text-align:right;padding:8px 10px;color:var(--color-text-muted);font-size:11px;text-transform:uppercase;letter-spacing:.06em;">Toggle</th>
        </tr>
      </thead>
      <tbody>
        {% for key, (job_id, label, interval) in job_map.items() %}
        {% set job_enabled = config['job_' + key] if config is mapping else config|attr('job_' + key) %}
        <tr style="border-bottom:1px solid var(--color-surface-subtle);">
          <td style="padding:10px;">{{ label }}</td>
          <td style="padding:10px;color:var(--color-text-muted);">every {{ interval }}</td>
          <td style="padding:10px;text-align:right;">
            <button
              class="btn btn-sm {% if job_enabled %}btn-primary{% else %}btn-secondary{% endif %}"
              style="min-width:52px;font-size:12px;"
              onclick="toggleJob('{{ key }}', this)">
              {% if job_enabled %}ON{% else %}OFF{% endif %}
            </button>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <!-- Activity log -->
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
      <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--color-text-muted);">
        Live Activity Log
      </div>
      <div id="logStatus" style="font-size:11px;color:var(--color-text-muted);">auto-refreshes every 10s</div>
    </div>
    <div id="activityLog"
         style="background:var(--color-surface-subtle);border-radius:6px;padding:14px;font-family:monospace;font-size:12px;max-height:340px;overflow-y:auto;">
      {% if logs %}
        {% for log in logs %}
        <div style="padding:3px 0;border-bottom:1px solid rgba(0,0,0,.04);">
          <span style="color:var(--color-text-muted);">{{ log.created_at.strftime('%H:%M:%S') }}</span>&nbsp;
          <span style="color:var(--color-primary);font-weight:600;">{{ log.job_type }}</span>&nbsp;
          {{ log.message }}
        </div>
        {% endfor %}
      {% else %}
        <div style="color:var(--color-text-muted);text-align:center;padding:20px;">
          No activity yet. Enable simulation to start generating data.
        </div>
      {% endif %}
    </div>
  </div>

</div>

<script>
function toggleMaster() {
  fetch('/settings/simulator/toggle', {method: 'POST'})
    .then(r => r.json())
    .then(data => {
      const btn = document.getElementById('masterToggle');
      if (data.enabled) {
        btn.textContent = '● Enabled';
        btn.className = 'btn btn-primary';
      } else {
        btn.textContent = '○ Disabled';
        btn.className = 'btn btn-secondary';
      }
      btn.dataset.enabled = data.enabled ? 'true' : 'false';
    });
}

function toggleJob(jobKey, btn) {
  fetch('/settings/simulator/job/' + jobKey, {method: 'POST'})
    .then(r => r.json())
    .then(data => {
      if (data.enabled) {
        btn.textContent = 'ON';
        btn.className = 'btn btn-sm btn-primary';
      } else {
        btn.textContent = 'OFF';
        btn.className = 'btn btn-sm btn-secondary';
      }
    });
}

function refreshLog() {
  fetch('/settings/simulator/log')
    .then(r => r.json())
    .then(entries => {
      const el = document.getElementById('activityLog');
      if (!entries.length) return;
      el.innerHTML = entries.map(e =>
        `<div style="padding:3px 0;border-bottom:1px solid rgba(0,0,0,.04);">` +
        `<span style="color:var(--color-text-muted);">${e.time}</span>&nbsp;` +
        `<span style="color:var(--color-primary);font-weight:600;">${e.job_type}</span>&nbsp;` +
        `${e.message}</div>`
      ).join('');
    });
}

setInterval(refreshLog, 10000);
</script>
{% endblock %}
```

- [ ] **Step 2: Commit**

```bash
git add app/templates/settings/simulator.html
git commit -m "feat: add simulator settings template with master/job toggles and activity log"
```

---

## Task 9: Wire Into App Factory and Nav

**Files:**
- Modify: `app/__init__.py`
- Modify: `app/templates/base.html`

- [ ] **Step 1: Register settings blueprint and start scheduler in `app/__init__.py`**

In `_register_blueprints(app)`, add after the last `app.register_blueprint(planning_bp)` call:

```python
    from app.blueprints.settings import settings_bp
    app.register_blueprint(settings_bp)
```

In `_init_extensions(app)`, add at the end of the function (after the `auto_login` block):

```python
    from app.simulator import start_scheduler
    start_scheduler(app)
```

- [ ] **Step 2: Add Settings link to grid nav in `app/templates/base.html`**

Find the last `<a href=...>` entry in the `grid-nav-dropdown` div (the Planning & Release link). Add this entry immediately after it:

```html
      <a href="{{ url_for('settings.simulator') }}" class="grid-nav-item">
        <div class="grid-nav-icon">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
        </div>
        <span>Settings</span>
      </a>
```

- [ ] **Step 3: Run the settings route tests (now blueprint is registered)**

```bash
.venv/bin/pytest tests/test_settings_routes.py -v
```

Expected: All 5 tests `PASS`.

- [ ] **Step 4: Run the full test suite**

```bash
.venv/bin/pytest tests/ -v
```

Expected: All tests pass, no regressions.

- [ ] **Step 5: Commit**

```bash
git add app/__init__.py app/templates/base.html
git commit -m "feat: wire simulator scheduler and settings blueprint into app factory and nav"
```

---

## Task 10: End-to-End Smoke Test

- [ ] **Step 1: Start the app**

```bash
.venv/bin/flask run
```

Expected: Server starts on port 5000 with no errors. Log should show `Simulator scheduler started (all jobs paused)`.

- [ ] **Step 2: Visit the settings page**

Open `http://127.0.0.1:5000/settings/simulator` in a browser.

Expected: Page loads showing "Demo Simulation ○ Disabled", 5 job rows all ON, empty activity log.

- [ ] **Step 3: Enable the simulator**

Click "○ Disabled". Expected: Button changes to "● Enabled". The seeder runs in the background (check Flask logs for `Simulator seed complete for org ...`).

- [ ] **Step 4: Verify seeded data**

Navigate to `http://127.0.0.1:5000/execution/runs`. After ~1 minute, test runs should start appearing. Navigate to `/execution/bugs` — bugs should appear within 2 minutes.

- [ ] **Step 5: Check the activity log**

Return to `/settings/simulator`. The activity log should show entries like:
```
14:32:01  write_test_case  Alice Chen added "Verify login flow with valid credentials" → Login & Auth
14:31:20  automation_run   CI automation queued: build-4821 on main → API Integration (8 tests)
```

- [ ] **Step 6: Toggle a job off**

Click OFF on "Write test cases". Verify no new `write_test_case` entries appear in the log after 45s.

- [ ] **Step 7: Disable the simulator**

Click "● Enabled". Expected: Button changes to "○ Disabled". All job activity stops.

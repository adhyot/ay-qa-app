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

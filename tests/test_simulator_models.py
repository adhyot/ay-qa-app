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

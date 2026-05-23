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

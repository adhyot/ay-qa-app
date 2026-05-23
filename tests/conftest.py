import pytest
from app import create_app
from app.extensions import db as _db
from app.models.user import User
from app.models.organization import Organization


@pytest.fixture(scope='session')
def app():
    app = create_app('testing')
    with app.app_context():
        _db.create_all()
        org = Organization(name='Test Org', slug='test-org')
        _db.session.add(org)
        _db.session.flush()
        user = User(
            email='test@test.com',
            full_name='Test User',
            org_id=org.id,
            role='qa_engineer',
        )
        user.set_password('password123')
        _db.session.add(user)
        _db.session.commit()
        yield app
        _db.drop_all()


@pytest.fixture(scope='session')
def client(app):
    return app.test_client()

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

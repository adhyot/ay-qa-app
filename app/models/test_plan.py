from app.extensions import db
from app.models.base import BaseModel


class TestPlan(BaseModel):
    __tablename__ = 'test_plans'

    name = db.Column(db.String(255), nullable=False)
    release_version = db.Column(db.String(100))
    sprint_name = db.Column(db.String(255))
    status = db.Column(db.String(20), default='draft')  # draft, active, in_review, signed_off, archived
    target_date = db.Column(db.Date)
    risk_score = db.Column(db.Float)
    risk_summary = db.Column(db.Text)
    confluence_page_id = db.Column(db.String(255))
    confluence_sync_at = db.Column(db.DateTime)
    sign_off_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    sign_off_at = db.Column(db.DateTime)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))

    signer = db.relationship('User', foreign_keys=[sign_off_by])
    creator = db.relationship('User', foreign_keys=[created_by])
    items = db.relationship('TestPlanItem', back_populates='plan', lazy='dynamic')

    def __repr__(self):
        return f'<TestPlan {self.name}>'


class TestPlanItem(BaseModel):
    __tablename__ = 'test_plan_items'

    plan_id = db.Column(db.String(36), db.ForeignKey('test_plans.id'), nullable=False)
    suite_id = db.Column(db.String(36), db.ForeignKey('test_suites.id'))
    test_case_id = db.Column(db.String(36), db.ForeignKey('test_cases.id'))
    coverage_type = db.Column(db.String(20), default='in_scope')  # in_scope, out_of_scope, risk_based
    notes = db.Column(db.Text)

    plan = db.relationship('TestPlan', back_populates='items')
    suite = db.relationship('TestSuite')
    test_case = db.relationship('TestCase')


class Initiative(BaseModel):
    __tablename__ = 'initiatives'

    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    jira_epic_key = db.Column(db.String(100))
    jira_url = db.Column(db.String(500))
    coverage_pct = db.Column(db.Float, default=0.0)
    owner_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    status = db.Column(db.String(30), default='active')  # active, completed, on_hold, cancelled
    target_date = db.Column(db.Date)

    owner = db.relationship('User', foreign_keys=[owner_id])

    def __repr__(self):
        return f'<Initiative {self.name}>'


class Release(BaseModel):
    __tablename__ = 'releases'

    version = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(255))
    target_date = db.Column(db.Date)
    status = db.Column(db.String(30), default='planning')  # planning, in_progress, released, cancelled
    coverage_pct = db.Column(db.Float, default=0.0)
    risk_score = db.Column(db.Float)          # 0–10, AI computed
    risk_summary = db.Column(db.Text)
    sign_off_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    sign_off_at = db.Column(db.DateTime)
    confluence_page_id = db.Column(db.String(255))
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))

    signer = db.relationship('User', foreign_keys=[sign_off_by])
    creator = db.relationship('User', foreign_keys=[created_by])

    @property
    def risk_level(self):
        if self.risk_score is None:
            return 'unknown'
        if self.risk_score >= 7:
            return 'high'
        if self.risk_score >= 4:
            return 'medium'
        return 'low'

    def __repr__(self):
        return f'<Release {self.version}>'

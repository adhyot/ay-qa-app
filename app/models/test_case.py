from app.extensions import db
from app.models.base import BaseModel


class TestSuite(BaseModel):
    __tablename__ = 'test_suites'

    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    tags = db.Column(db.JSON, default=list)
    owner_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    github_repo = db.Column(db.String(500))
    framework = db.Column(db.String(100))  # pytest, selenium, playwright

    owner = db.relationship('User', foreign_keys=[owner_id])
    test_cases = db.relationship('TestCase', back_populates='suite', lazy='dynamic')
    test_runs = db.relationship('TestRun', back_populates='suite', lazy='dynamic')

    @property
    def total_cases(self):
        return self.test_cases.filter_by(is_deleted=False).count()

    @property
    def automated_cases(self):
        return self.test_cases.filter_by(is_deleted=False, type='automated').count()

    @property
    def coverage_pct(self):
        total = self.total_cases
        return round((self.automated_cases / total * 100), 1) if total > 0 else 0.0

    def __repr__(self):
        return f'<TestSuite {self.name}>'


class TestCase(BaseModel):
    __tablename__ = 'test_cases'

    suite_id = db.Column(db.String(36), db.ForeignKey('test_suites.id'), nullable=False, index=True)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    steps = db.Column(db.JSON, default=list)  # [{order, action, expected_result}]
    priority = db.Column(db.String(20), default='medium')  # critical, high, medium, low
    type = db.Column(db.String(20), default='manual')      # manual, automated, hybrid
    automation_script_path = db.Column(db.String(500))
    tags = db.Column(db.JSON, default=list)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    updated_by = db.Column(db.String(36), db.ForeignKey('users.id'))

    suite = db.relationship('TestSuite', back_populates='test_cases')
    creator = db.relationship('User', foreign_keys=[created_by])

    def __repr__(self):
        return f'<TestCase {self.title[:50]}>'

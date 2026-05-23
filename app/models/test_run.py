from app.extensions import db
from app.models.base import BaseModel


class TestRun(BaseModel):
    __tablename__ = 'test_runs'

    suite_id = db.Column(db.String(36), db.ForeignKey('test_suites.id'), nullable=False, index=True)
    environment_id = db.Column(db.String(36), db.ForeignKey('environments.id'))
    triggered_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    trigger_type = db.Column(db.String(20), default='manual')  # manual, scheduled, ci_cd, api
    status = db.Column(db.String(20), default='queued')  # queued, running, passed, failed, cancelled, partial
    ci_build_id = db.Column(db.String(255))
    ci_pipeline_url = db.Column(db.String(500))
    branch = db.Column(db.String(255))
    config = db.Column(db.JSON, default=dict)
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)
    pass_count = db.Column(db.Integer, default=0)
    fail_count = db.Column(db.Integer, default=0)
    skip_count = db.Column(db.Integer, default=0)
    total_count = db.Column(db.Integer, default=0)
    ai_root_cause = db.Column(db.Text)

    suite = db.relationship('TestSuite', back_populates='test_runs')
    triggerer = db.relationship('User', foreign_keys=[triggered_by])
    results = db.relationship('TestRunResult', back_populates='run', lazy='dynamic')
    environment = db.relationship('Environment', foreign_keys=[environment_id])

    @property
    def pass_rate(self):
        return round((self.pass_count / self.total_count * 100), 1) if self.total_count > 0 else 0.0

    @property
    def duration_seconds(self):
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None

    def __repr__(self):
        return f'<TestRun {self.id[:8]} {self.status}>'


class TestRunResult(BaseModel):
    __tablename__ = 'test_run_results'

    run_id = db.Column(db.String(36), db.ForeignKey('test_runs.id'), nullable=False, index=True)
    test_case_id = db.Column(db.String(36), db.ForeignKey('test_cases.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # passed, failed, skipped, error, flaky
    duration_ms = db.Column(db.Integer)
    error_message = db.Column(db.Text)
    stack_trace = db.Column(db.Text)
    screenshot_url = db.Column(db.String(500))
    retry_count = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)

    run = db.relationship('TestRun', back_populates='results')
    test_case = db.relationship('TestCase')

    def __repr__(self):
        return f'<TestRunResult {self.test_case_id[:8]} {self.status}>'

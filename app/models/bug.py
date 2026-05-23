from app.extensions import db
from app.models.base import BaseModel


class Bug(BaseModel):
    __tablename__ = 'bugs'

    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    severity = db.Column(db.String(20), default='major')   # blocker, critical, major, minor, trivial
    priority = db.Column(db.String(20), default='medium')  # critical, high, medium, low
    status = db.Column(db.String(20), default='open')      # open, in_progress, resolved, wont_fix, duplicate
    assigned_to = db.Column(db.String(36), db.ForeignKey('users.id'))
    reported_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    run_result_id = db.Column(db.String(36), db.ForeignKey('test_run_results.id'))
    jira_ticket_id = db.Column(db.String(100))
    jira_ticket_url = db.Column(db.String(500))
    labels = db.Column(db.JSON, default=list)
    ai_summary = db.Column(db.Text)
    ai_root_cause = db.Column(db.Text)

    assignee = db.relationship('User', foreign_keys=[assigned_to])
    reporter = db.relationship('User', foreign_keys=[reported_by])
    run_result = db.relationship('TestRunResult')

    SEVERITY_ORDER = {'blocker': 0, 'critical': 1, 'major': 2, 'minor': 3, 'trivial': 4}

    @property
    def severity_level(self):
        return self.SEVERITY_ORDER.get(self.severity, 99)

    def __repr__(self):
        return f'<Bug {self.severity}: {self.title[:50]}>'

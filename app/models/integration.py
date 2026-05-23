from app.extensions import db
from app.models.base import BaseModel

INTEGRATION_TYPES = ('github', 'jira', 'confluence', 'datadog', 'slack', 'custom')


class Integration(BaseModel):
    __tablename__ = 'integrations'

    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(30), nullable=False)
    base_url = db.Column(db.String(500))
    credentials = db.Column(db.JSON, default=dict)  # token, api_key etc — encrypt in prod
    config = db.Column(db.JSON, default=dict)        # project_key, repo, board_id etc
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    health_status = db.Column(db.String(20), default='unknown')  # healthy, degraded, down, unknown
    last_health_check = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Integration {self.type}:{self.name}>'

from app.extensions import db
from app.models.base import BaseModel


class Environment(BaseModel):
    __tablename__ = 'environments'

    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(30), default='staging')  # local, staging, production, ephemeral
    base_url = db.Column(db.String(500))
    health_status = db.Column(db.String(20), default='unknown')  # healthy, degraded, down, unknown
    last_health_check = db.Column(db.DateTime)
    config = db.Column(db.JSON, default=dict)
    tags = db.Column(db.JSON, default=list)

    fixtures = db.relationship('DataFixture', back_populates='environment', lazy='dynamic')

    def __repr__(self):
        return f'<Environment {self.name}>'


class DataFixture(BaseModel):
    __tablename__ = 'data_fixtures'

    name = db.Column(db.String(255), nullable=False)
    environment_id = db.Column(db.String(36), db.ForeignKey('environments.id'))
    fixture_type = db.Column(db.String(30), default='sql_script')  # sql_script, json_seed, api_call, custom
    content = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    last_applied_at = db.Column(db.DateTime)

    environment = db.relationship('Environment', back_populates='fixtures')

    def __repr__(self):
        return f'<DataFixture {self.name}>'

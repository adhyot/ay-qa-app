from app.extensions import db
from app.models.base import BaseModel

ARTIFACT_TYPES = ('test_case', 'test_suite', 'job', 'service', 'pipeline')


class Allocation(BaseModel):
    __tablename__ = 'allocations'

    artifact_type = db.Column(db.String(30), nullable=False)  # test_case, job, service
    artifact_id = db.Column(db.String(36))
    artifact_name = db.Column(db.String(500), nullable=False)
    owner_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    team = db.Column(db.String(255))
    notes = db.Column(db.Text)

    owner = db.relationship('User', foreign_keys=[owner_id])

    def __repr__(self):
        return f'<Allocation {self.artifact_type}:{self.artifact_name[:50]}>'

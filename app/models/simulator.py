from datetime import datetime, timezone
from app.extensions import db
from app.models.base import generate_uuid


class SimulatorConfig(db.Model):
    __tablename__ = 'simulator_configs'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    org_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False, unique=True)
    enabled = db.Column(db.Boolean, default=False, nullable=False)
    seeded = db.Column(db.Boolean, default=False, nullable=False)
    job_write_test_case = db.Column(db.Boolean, default=True, nullable=False)
    job_start_run = db.Column(db.Boolean, default=True, nullable=False)
    job_complete_run = db.Column(db.Boolean, default=True, nullable=False)
    job_file_bug = db.Column(db.Boolean, default=True, nullable=False)
    job_automation_run = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SimulatorLog(db.Model):
    __tablename__ = 'simulator_logs'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    org_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False, index=True)
    job_type = db.Column(db.String(30), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

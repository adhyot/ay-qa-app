from app.extensions import db
from app.models.base import BaseModel, generate_uuid
from datetime import datetime, timezone


class Organization(db.Model):
    __tablename__ = 'organizations'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    plan = db.Column(db.String(20), default='free')  # free, starter, pro, enterprise
    settings = db.Column(db.JSON, default=dict)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    members = db.relationship('OrganizationMember', back_populates='organization', lazy='dynamic')
    users = db.relationship('User', back_populates='organization', lazy='dynamic')

    def __repr__(self):
        return f'<Organization {self.slug}>'


class OrganizationMember(db.Model):
    __tablename__ = 'organization_members'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    org_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(30), default='qa_engineer')
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    organization = db.relationship('Organization', back_populates='members')
    user = db.relationship('User', back_populates='memberships')

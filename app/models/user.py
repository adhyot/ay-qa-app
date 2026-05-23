from datetime import datetime, timezone
from flask_login import UserMixin
import bcrypt
from app.extensions import db
from app.models.base import generate_uuid

ROLES = ('admin', 'qa_manager', 'qa_engineer', 'viewer')


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    org_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=True, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), default='qa_engineer', nullable=False)
    avatar_url = db.Column(db.String(500))
    last_login_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    organization = db.relationship('Organization', back_populates='users')
    memberships = db.relationship('OrganizationMember', back_populates='user', lazy='dynamic')

    def set_password(self, password: str):
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def record_login(self):
        self.last_login_at = datetime.now(timezone.utc)
        db.session.commit()

    @property
    def initials(self):
        parts = self.full_name.split()
        return ''.join(p[0].upper() for p in parts[:2]) if parts else '?'

    def __repr__(self):
        return f'<User {self.email}>'

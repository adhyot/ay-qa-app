from app.extensions import db
from app.models.base import BaseModel


class Notification(BaseModel):
    __tablename__ = 'notifications'

    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    type = db.Column(db.String(30), nullable=False)  # run_complete, bug_created, sign_off_needed, env_down, ai_insight
    title = db.Column(db.String(500), nullable=False)
    body = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    link = db.Column(db.String(500))

    user = db.relationship('User', foreign_keys=[user_id])

    def __repr__(self):
        return f'<Notification {self.type}: {self.title[:50]}>'

from app.extensions import db
from app.models.base import BaseModel


class SprintRetro(BaseModel):
    __tablename__ = 'sprint_retros'

    sprint_name = db.Column(db.String(255), nullable=False)
    sprint_number = db.Column(db.Integer)
    date = db.Column(db.Date)
    status = db.Column(db.String(20), default='open')  # open, completed
    what_went_well = db.Column(db.Text)
    what_to_improve = db.Column(db.Text)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))

    creator = db.relationship('User', foreign_keys=[created_by])
    action_items = db.relationship('RetroActionItem', back_populates='retro', lazy='dynamic')

    @property
    def open_action_count(self):
        return self.action_items.filter_by(status='open', is_deleted=False).count()

    def __repr__(self):
        return f'<SprintRetro {self.sprint_name}>'


class RetroActionItem(BaseModel):
    __tablename__ = 'retro_action_items'

    retro_id = db.Column(db.String(36), db.ForeignKey('sprint_retros.id'), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    owner_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    due_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='open')  # open, done
    priority = db.Column(db.String(20), default='medium')

    retro = db.relationship('SprintRetro', back_populates='action_items')
    owner = db.relationship('User', foreign_keys=[owner_id])

    def __repr__(self):
        return f'<RetroActionItem {self.title[:50]}>'

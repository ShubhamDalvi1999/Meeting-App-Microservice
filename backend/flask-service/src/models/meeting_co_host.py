from datetime import datetime, timezone
from .. import db

class MeetingCoHost(db.Model):
    __tablename__ = 'meeting_co_hosts'
    
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permissions = db.Column(db.String(255), nullable=True)  # comma-separated list of permissions
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = db.relationship('User', backref=db.backref('co_hosted_meetings', lazy=True))
    
    def __init__(self, meeting_id, user_id):
        self.meeting_id = meeting_id
        self.user_id = user_id
        
    def to_dict(self):
        return {
            'id': self.id,
            'meeting_id': self.meeting_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 
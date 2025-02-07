from datetime import datetime, UTC
from .. import db

class MeetingAuditLog(db.Model):
    __tablename__ = 'meeting_audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # created, joined, left, ended, etc.
    details = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    
    # Relationships
    meeting = db.relationship('Meeting', backref=db.backref('audit_logs', lazy=True))
    user = db.relationship('User', backref=db.backref('meeting_actions', lazy=True))
    
    def __init__(self, meeting_id, user_id, action, details=None):
        self.meeting_id = meeting_id
        self.user_id = user_id
        self.action = action
        self.details = details
        
    def to_dict(self):
        return {
            'id': self.id,
            'meeting_id': self.meeting_id,
            'user_id': self.user_id,
            'action': self.action,
            'details': self.details,
            'created_at': self.created_at.isoformat()
        } 
from datetime import datetime, timezone
from .. import db
from ..schemas.meeting import MeetingCreate, MeetingUpdate, MeetingResponse

class Meeting(db.Model):
    __tablename__ = 'meetings'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    ended_at = db.Column(db.DateTime, nullable=True)
    
    # New fields
    meeting_type = db.Column(db.String(20), nullable=False, default='regular')  # regular, recurring, private
    max_participants = db.Column(db.Integer, nullable=True)
    requires_approval = db.Column(db.Boolean, nullable=False, default=False)
    is_recorded = db.Column(db.Boolean, nullable=False, default=False)
    recording_url = db.Column(db.String(500), nullable=True)
    recurring_pattern = db.Column(db.String(50), nullable=True)  # daily, weekly, monthly, custom
    parent_meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), nullable=True)  # For recurring meetings

    # Relationships
    creator = db.relationship('User', backref=db.backref('created_meetings', lazy=True))
    participants = db.relationship('MeetingParticipant', backref='meeting', lazy=True, cascade='all, delete-orphan')
    co_hosts = db.relationship('MeetingCoHost', backref='meeting', lazy=True, cascade='all, delete-orphan')
    child_meetings = db.relationship('Meeting', backref=db.backref('parent_meeting', remote_side=[id]))

    def __init__(self, title, description, start_time, end_time, created_by, meeting_type='regular', 
                 max_participants=None, requires_approval=False, is_recorded=False):
        self.title = title
        self.description = description
        self.start_time = start_time
        self.end_time = end_time
        self.created_by = created_by
        self.meeting_type = meeting_type
        self.max_participants = max_participants
        self.requires_approval = requires_approval
        self.is_recorded = is_recorded

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'meeting_type': self.meeting_type,
            'max_participants': self.max_participants,
            'requires_approval': self.requires_approval,
            'is_recorded': self.is_recorded,
            'recording_url': self.recording_url,
            'recurring_pattern': self.recurring_pattern,
            'parent_meeting_id': self.parent_meeting_id
        }

    @classmethod
    def from_schema(cls, meeting_create: MeetingCreate, created_by: int):
        """Create a new meeting from a MeetingCreate schema"""
        return cls(
            title=meeting_create.title,
            description=meeting_create.description,
            start_time=meeting_create.start_time,
            end_time=meeting_create.end_time,
            created_by=created_by,
            meeting_type=meeting_create.meeting_type,
            max_participants=meeting_create.max_participants,
            requires_approval=meeting_create.requires_approval,
            is_recorded=meeting_create.is_recorded,
            recurring_pattern=meeting_create.recurring_pattern,
            parent_meeting_id=meeting_create.parent_meeting_id
        )

    def update_from_schema(self, meeting_update: MeetingUpdate):
        """Update meeting from a MeetingUpdate schema"""
        for field, value in meeting_update.model_dump(exclude_unset=True).items():
            setattr(self, field, value)

    def to_schema(self) -> MeetingResponse:
        """Convert meeting model to MeetingResponse schema"""
        response_data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'ended_at': self.ended_at,
            'meeting_type': self.meeting_type,
            'max_participants': self.max_participants,
            'requires_approval': self.requires_approval,
            'is_recorded': self.is_recorded,
            'recording_url': self.recording_url,
            'recurring_pattern': self.recurring_pattern,
            'parent_meeting_id': self.parent_meeting_id,
            'participant_count': len(self.participants),
            'co_hosts': [co_host.user_id for co_host in self.co_hosts]
        }
        return MeetingResponse.model_validate(response_data) 
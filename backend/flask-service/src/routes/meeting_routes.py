from flask import Blueprint, request, jsonify
from ..models.meeting import Meeting
from ..models.meeting_participant import MeetingParticipant
from ..schemas.meeting import MeetingCreate, MeetingUpdate
from ..schemas.participant import ParticipantCreate, ParticipantUpdate, ParticipantJoin, ParticipantLeave
from .. import db
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from functools import wraps
from datetime import datetime, UTC

bp = Blueprint('meetings', __name__)

def validate_schema(schema_class):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = request.get_json()
                schema = schema_class(**data)
                return f(schema, *args, **kwargs)
            except ValidationError as e:
                return jsonify({"error": "Validation error", "details": e.errors()}), 400
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        return decorated_function
    return decorator

@bp.route('/meetings', methods=['POST'])
@validate_schema(MeetingCreate)
def create_meeting(data: MeetingCreate):
    try:
        # Assuming we have the user_id from authentication
        user_id = 1  # Replace with actual authenticated user_id
        meeting = Meeting.from_schema(data, created_by=user_id)
        db.session.add(meeting)
        db.session.commit()
        return jsonify(meeting.to_schema().model_dump()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Failed to create meeting"}), 400

@bp.route('/meetings/<int:meeting_id>', methods=['PUT'])
@validate_schema(MeetingUpdate)
def update_meeting(data: MeetingUpdate, meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    try:
        meeting.update_from_schema(data)
        db.session.commit()
        return jsonify(meeting.to_schema().model_dump())
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Failed to update meeting"}), 400

@bp.route('/meetings/<int:meeting_id>/participants', methods=['POST'])
@validate_schema(ParticipantCreate)
def add_participant(data: ParticipantCreate, meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    try:
        participant = MeetingParticipant.from_schema(data)
        db.session.add(participant)
        db.session.commit()
        return jsonify(participant.to_schema().model_dump()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Failed to add participant"}), 400

@bp.route('/meetings/<int:meeting_id>/participants/<int:user_id>', methods=['PUT'])
@validate_schema(ParticipantUpdate)
def update_participant(data: ParticipantUpdate, meeting_id, user_id):
    participant = MeetingParticipant.query.filter_by(
        meeting_id=meeting_id,
        user_id=user_id
    ).first_or_404()
    
    try:
        participant.update_from_schema(data)
        db.session.commit()
        return jsonify(participant.to_schema().model_dump())
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Failed to update participant"}), 400

@bp.route('/meetings/<int:meeting_id>/join', methods=['POST'])
@validate_schema(ParticipantJoin)
def join_meeting(data: ParticipantJoin, meeting_id):
    participant = MeetingParticipant.query.filter_by(
        meeting_id=meeting_id,
        user_id=data.user_id
    ).first_or_404()
    
    if participant.is_banned:
        return jsonify({"error": "You are banned from this meeting"}), 403
    
    if participant.status != 'approved' and Meeting.query.get(meeting_id).requires_approval:
        return jsonify({"error": "Waiting for approval"}), 403
    
    participant.record_join(data.connection_quality)
    return jsonify(participant.to_schema().model_dump())

@bp.route('/meetings/<int:meeting_id>/leave', methods=['POST'])
@validate_schema(ParticipantLeave)
def leave_meeting(data: ParticipantLeave, meeting_id):
    participant = MeetingParticipant.query.filter_by(
        meeting_id=meeting_id,
        user_id=data.user_id
    ).first_or_404()
    
    participant.record_leave(
        total_time=data.total_time,
        participation_score=data.participation_score,
        feedback=data.feedback
    )
    return jsonify(participant.to_schema().model_dump()) 
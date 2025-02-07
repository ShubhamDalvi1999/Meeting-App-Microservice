from flask import Blueprint, request, jsonify
from functools import wraps
import jwt
import os
from datetime import datetime, UTC
import bleach

from ..models import db, User, Meeting, MeetingParticipant, MeetingCoHost, MeetingAuditLog

meetings_bp = Blueprint('meetings', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': 'Invalid token format'}), 401
            
        try:
            token = token.split('Bearer ')[1]
            data = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired', 'code': 'token_expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token', 'code': 'token_invalid'}), 401
        except jwt.InvalidKeyError:
            return jsonify({'error': 'Invalid signing key', 'code': 'invalid_key'}), 401
        except jwt.InvalidAlgorithmError:
            return jsonify({'error': 'Invalid algorithm specified', 'code': 'invalid_algorithm'}), 401
        except Exception as e:
            return jsonify({'error': 'Authentication error', 'code': 'auth_error'}), 401
            
        return f(current_user, *args, **kwargs)
        
    return decorated

@meetings_bp.route('/create', methods=['POST'])
@token_required
def create_meeting(current_user):
    """Create a new meeting."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        required_fields = ['title', 'description', 'start_time', 'end_time']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Validate title and description
        title = bleach.clean(data['title'].strip())
        description = bleach.clean(data['description'].strip())
        
        if not title:
            return jsonify({'error': 'Meeting title cannot be empty'}), 400
            
        if len(title) > 200:
            return jsonify({'error': 'Meeting title too long (max 200 characters)'}), 400
            
        if len(description) > 2000:
            return jsonify({'error': 'Meeting description too long (max 2000 characters)'}), 400

        try:
            start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
            
            if not start_time.tzinfo or not end_time.tzinfo:
                return jsonify({'error': 'Timezone information is required'}), 400
                
        except ValueError:
            return jsonify({'error': 'Invalid datetime format. Please use ISO format'}), 400

        current_time = datetime.now(UTC)
        
        # Enhanced time validations
        if start_time < current_time:
            return jsonify({'error': 'Meeting cannot start in the past'}), 400
            
        if start_time >= end_time:
            return jsonify({'error': 'Start time must be before end time'}), 400
            
        # Validate reasonable time ranges
        duration = end_time - start_time
        if duration.total_seconds() < 300:  # 5 minutes minimum
            return jsonify({'error': 'Meeting must be at least 5 minutes long'}), 400
            
        if duration.total_seconds() > 86400:  # 24 hours maximum
            return jsonify({'error': 'Meeting cannot be longer than 24 hours'}), 400
            
        # Check if start time is too far in the future
        if (start_time - current_time).days > 365:
            return jsonify({'error': 'Cannot schedule meetings more than 1 year in advance'}), 400
            
        # Validate meeting type and settings
        meeting_type = data.get('meeting_type', 'regular')
        if meeting_type not in ['regular', 'recurring', 'private']:
            return jsonify({'error': 'Invalid meeting type'}), 400
            
        max_participants = data.get('max_participants')
        if max_participants is not None:
            if not isinstance(max_participants, int) or max_participants <= 0:
                return jsonify({'error': 'Invalid maximum participants value'}), 400
                
        requires_approval = data.get('requires_approval', False)
        is_recorded = data.get('is_recorded', False)
        
        # Handle recurring meeting pattern
        recurring_pattern = None
        if meeting_type == 'recurring':
            recurring_pattern = data.get('recurring_pattern')
            if not recurring_pattern or recurring_pattern not in ['daily', 'weekly', 'monthly', 'custom']:
                return jsonify({'error': 'Invalid recurring pattern for recurring meeting'}), 400
            
        # Check for overlapping meetings for the user
        user_meetings = Meeting.query.filter(
            Meeting.created_by == current_user.id,
            Meeting.ended_at.is_(None),
            Meeting.end_time > start_time,
            Meeting.start_time < end_time
        ).first()
        
        if user_meetings:
            return jsonify({'error': 'You have another meeting scheduled during this time'}), 400
            
        # Check total number of active meetings for user
        active_meetings_count = Meeting.query.filter(
            Meeting.created_by == current_user.id,
            Meeting.ended_at.is_(None)
        ).count()
        
        if active_meetings_count >= 50:
            return jsonify({'error': 'You have reached the maximum limit of active meetings'}), 400
        
        # Create the meeting
        meeting = Meeting(
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            created_by=current_user.id,
            meeting_type=meeting_type,
            max_participants=max_participants,
            requires_approval=requires_approval,
            is_recorded=is_recorded
        )
        
        if recurring_pattern:
            meeting.recurring_pattern = recurring_pattern
            
        db.session.add(meeting)
        
        # Add co-hosts if specified
        co_host_ids = data.get('co_hosts', [])
        for co_host_id in co_host_ids:
            if co_host_id != current_user.id:
                co_host = MeetingCoHost(meeting_id=meeting.id, user_id=co_host_id)
                db.session.add(co_host)
                
        # Log the creation
        audit_log = MeetingAuditLog(
            meeting_id=meeting.id,
            user_id=current_user.id,
            action='created',
            details={
                'meeting_type': meeting_type,
                'requires_approval': requires_approval,
                'is_recorded': is_recorded,
                'recurring_pattern': recurring_pattern
            }
        )
        db.session.add(audit_log)
        
        db.session.commit()
        
        return jsonify(meeting.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Server error occurred while creating meeting'}), 500

@meetings_bp.route('/join/<int:id>', methods=['GET'])
@token_required
def join_meeting(current_user, id):
    try:
        if id <= 0:
            return jsonify({'error': 'Invalid meeting ID'}), 400
            
        meeting = Meeting.query.get(id)
        
        if not meeting:
            return jsonify({'error': 'Meeting not found'}), 404
            
        # Check if meeting has ended
        if meeting.ended_at:
            return jsonify({'error': 'Meeting has already ended'}), 400

        # Check if meeting hasn't started yet
        current_time = datetime.now(UTC)
        if current_time < meeting.start_time:
            time_until_start = (meeting.start_time - current_time).total_seconds()
            if time_until_start > 300:  # More than 5 minutes before start
                return jsonify({
                    'error': 'Meeting has not started yet',
                    'starts_in_minutes': round(time_until_start / 60)
                }), 400

        # Check if meeting has exceeded its end time
        if current_time > meeting.end_time:
            return jsonify({'error': 'Meeting has exceeded its scheduled end time'}), 400

        # Check maximum participants limit
        current_participants = MeetingParticipant.query.filter_by(
            meeting_id=meeting.id,
            left_at=None
        ).count()
        if meeting.max_participants and current_participants >= meeting.max_participants:
            return jsonify({'error': 'Meeting has reached maximum participants'}), 400

        # Check if user is banned
        participant = MeetingParticipant.query.filter_by(
            meeting_id=meeting.id,
            user_id=current_user.id
        ).first()
        
        if participant and participant.is_banned:
            return jsonify({'error': 'You have been banned from this meeting'}), 403

        # Check concurrent meetings
        active_participation = MeetingParticipant.query.join(Meeting).filter(
            MeetingParticipant.user_id == current_user.id,
            Meeting.ended_at.is_(None),
            Meeting.id != meeting.id,
            MeetingParticipant.left_at.is_(None)
        ).first()
        
        if active_participation:
            return jsonify({'error': 'You are already in another active meeting'}), 400

        # Determine participant role
        participant_role = 'attendee'
        if meeting.created_by == current_user.id:
            participant_role = 'host'
        elif MeetingCoHost.query.filter_by(meeting_id=meeting.id, user_id=current_user.id).first():
            participant_role = 'co-host'

        # Handle participant joining
        if meeting.created_by != current_user.id:
            if not participant:
                participant = MeetingParticipant(
                    meeting_id=meeting.id,
                    user_id=current_user.id,
                    status='pending' if meeting.requires_approval else 'approved',
                    role=participant_role,
                    joined_at=current_time if not meeting.requires_approval else None
                )
                db.session.add(participant)
            else:
                # Update rejoin time if they previously left
                participant.joined_at = current_time if not meeting.requires_approval else None
                participant.left_at = None
                participant.role = participant_role
                
            db.session.commit()

            # If waiting room is enabled
            if meeting.requires_approval and participant.status == 'pending':
                return jsonify({
                    'message': 'Waiting for host approval',
                    'status': 'waiting'
                }), 202

        # Log the join attempt
        audit_log = MeetingAuditLog(
            meeting_id=meeting.id,
            user_id=current_user.id,
            action='joined',
            details={
                'role': participant_role,
                'status': participant.status if participant else 'host'
            }
        )
        db.session.add(audit_log)
        db.session.commit()

        # Return meeting details with participant info
        meeting_dict = meeting.to_dict()
        meeting_dict.update({
            'is_creator': meeting.created_by == current_user.id,
            'is_co_host': participant_role == 'co-host',
            'role': participant_role,
            'participant_count': current_participants,
            'time_remaining_minutes': round((meeting.end_time - current_time).total_seconds() / 60)
        })
        return jsonify(meeting_dict), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Server error occurred while joining meeting'}), 500

@meetings_bp.route('/list', methods=['GET'])
@token_required
def list_meetings(current_user):
    try:
        # Get query parameters for filtering
        active_only = request.args.get('active_only', type=lambda v: v.lower() == 'true', default=True)
        
        print(f"Fetching meetings for user {current_user.id}, active_only={active_only}")
        
        # First, get meetings where user is creator
        creator_meetings = Meeting.query.filter(Meeting.created_by == current_user.id)
        if active_only:
            creator_meetings = creator_meetings.filter(Meeting.ended_at.is_(None))
        creator_meetings = creator_meetings.all()
        print(f"Found {len(creator_meetings)} meetings as creator")

        # Then, get meetings where user is participant
        participant_meetings = Meeting.query.join(MeetingParticipant).filter(
            MeetingParticipant.user_id == current_user.id
        )
        if active_only:
            participant_meetings = participant_meetings.filter(Meeting.ended_at.is_(None))
        participant_meetings = participant_meetings.all()
        print(f"Found {len(participant_meetings)} meetings as participant")

        # Combine and sort meetings
        all_meetings = sorted(
            set(creator_meetings + participant_meetings),
            key=lambda m: m.created_at,
            reverse=True
        )
        
        print(f"Total unique meetings: {len(all_meetings)}")
        return jsonify([meeting.to_dict() for meeting in all_meetings])
        
    except Exception as e:
        import traceback
        print(f"Error in list_meetings: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        db.session.rollback()
        return jsonify({'error': 'Server error occurred while fetching meetings'}), 500

@meetings_bp.route('/<int:id>', methods=['GET'])
@token_required
def get_meeting(current_user, id):
    try:
        meeting = Meeting.query.get(id)
        
        if not meeting:
            return jsonify({'error': 'Meeting not found'}), 404
            
        # Check if user has access to the meeting
        if meeting.created_by != current_user.id and current_user.id not in [p.user_id for p in meeting.participants]:
            return jsonify({'error': 'Access denied'}), 403
            
        return jsonify(meeting.to_dict())
        
    except Exception as e:
        return jsonify({'error': 'Server error occurred while fetching meeting'}), 500

@meetings_bp.route('/<int:id>', methods=['DELETE'])
@token_required
def delete_meeting(current_user, id):
    try:
        meeting = Meeting.query.get(id)
        
        if not meeting:
            return jsonify({'error': 'Meeting not found'}), 404
            
        if meeting.created_by != current_user.id:
            return jsonify({'error': 'Only the host can delete the meeting'}), 403
            
        db.session.delete(meeting)
        db.session.commit()
        
        return jsonify({'message': 'Meeting deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Server error occurred while deleting meeting'}), 500

@meetings_bp.route('/<int:id>/end', methods=['POST'])
@token_required
def end_meeting(current_user, id):
    try:
        meeting = Meeting.query.get(id)
        
        if not meeting:
            return jsonify({'error': 'Meeting not found'}), 404
            
        if meeting.created_by != current_user.id:
            return jsonify({'error': 'Only the host can end the meeting'}), 403
            
        meeting.ended_at = datetime.now(UTC)
        db.session.commit()
        
        return jsonify({'message': 'Meeting ended successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Server error occurred while ending meeting'}), 500

@meetings_bp.route('/<int:id>/co-hosts', methods=['POST'])
@token_required
def add_co_host(current_user, id):
    try:
        meeting = Meeting.query.get(id)
        
        if not meeting:
            return jsonify({'error': 'Meeting not found'}), 404
            
        if meeting.created_by != current_user.id:
            return jsonify({'error': 'Only the host can add co-hosts'}), 403
            
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({'error': 'No user_id provided'}), 400
            
        user_id = data['user_id']
        
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Check if already a co-host
        existing_co_host = MeetingCoHost.query.filter_by(
            meeting_id=id,
            user_id=user_id
        ).first()
        
        if existing_co_host:
            return jsonify({'error': 'User is already a co-host'}), 400
            
        co_host = MeetingCoHost(meeting_id=id, user_id=user_id)
        db.session.add(co_host)
        
        # Log the action
        audit_log = MeetingAuditLog(
            meeting_id=id,
            user_id=current_user.id,
            action='added_co_host',
            details={'co_host_id': user_id}
        )
        db.session.add(audit_log)
        
        db.session.commit()
        
        return jsonify({'message': 'Co-host added successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Server error occurred while adding co-host'}), 500

@meetings_bp.route('/<int:id>/co-hosts/<int:user_id>', methods=['DELETE'])
@token_required
def remove_co_host(current_user, id, user_id):
    try:
        meeting = Meeting.query.get(id)
        
        if not meeting:
            return jsonify({'error': 'Meeting not found'}), 404
            
        if meeting.created_by != current_user.id:
            return jsonify({'error': 'Only the host can remove co-hosts'}), 403
            
        co_host = MeetingCoHost.query.filter_by(
            meeting_id=id,
            user_id=user_id
        ).first()
        
        if not co_host:
            return jsonify({'error': 'User is not a co-host'}), 404
            
        db.session.delete(co_host)
        
        # Log the action
        audit_log = MeetingAuditLog(
            meeting_id=id,
            user_id=current_user.id,
            action='removed_co_host',
            details={'co_host_id': user_id}
        )
        db.session.add(audit_log)
        
        db.session.commit()
        
        return jsonify({'message': 'Co-host removed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Server error occurred while removing co-host'}), 500

@meetings_bp.route('/<int:id>/waiting-room', methods=['GET'])
@token_required
def get_waiting_room(current_user, id):
    try:
        meeting = Meeting.query.get(id)
        
        if not meeting:
            return jsonify({'error': 'Meeting not found'}), 404
            
        # Check if user has permission to view waiting room
        if meeting.created_by != current_user.id and not MeetingCoHost.query.filter_by(
            meeting_id=id,
            user_id=current_user.id
        ).first():
            return jsonify({'error': 'Access denied'}), 403
            
        # Get waiting participants
        waiting_participants = MeetingParticipant.query.filter_by(
            meeting_id=id,
            status='pending'
        ).all()
        
        return jsonify({
            'waiting_participants': [
                {
                    'id': p.id,
                    'user': User.query.get(p.user_id).to_dict(),
                    'joined_at': p.created_at.isoformat()
                }
                for p in waiting_participants
            ]
        })
        
    except Exception as e:
        return jsonify({'error': 'Server error occurred while fetching waiting room'}), 500

@meetings_bp.route('/<int:id>/participants/<int:participant_id>/approve', methods=['POST'])
@token_required
def approve_participant(current_user, id, participant_id):
    try:
        meeting = Meeting.query.get(id)
        
        if not meeting:
            return jsonify({'error': 'Meeting not found'}), 404
            
        # Check if user has permission to approve participants
        if meeting.created_by != current_user.id and not MeetingCoHost.query.filter_by(
            meeting_id=id,
            user_id=current_user.id
        ).first():
            return jsonify({'error': 'Access denied'}), 403
            
        participant = MeetingParticipant.query.get(participant_id)
        
        if not participant or participant.meeting_id != id:
            return jsonify({'error': 'Participant not found'}), 404
            
        if participant.status != 'pending':
            return jsonify({'error': 'Participant is not in waiting room'}), 400
            
        # Check maximum participants limit
        current_participants = MeetingParticipant.query.filter_by(
            meeting_id=id,
            left_at=None,
            status='approved'
        ).count()
        
        if meeting.max_participants and current_participants >= meeting.max_participants:
            return jsonify({'error': 'Meeting has reached maximum participants'}), 400
            
        participant.status = 'approved'
        participant.joined_at = datetime.now(UTC)
        
        # Log the action
        audit_log = MeetingAuditLog(
            meeting_id=id,
            user_id=current_user.id,
            action='approved_participant',
            details={'participant_id': participant_id}
        )
        db.session.add(audit_log)
        
        db.session.commit()
        
        return jsonify({'message': 'Participant approved successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Server error occurred while approving participant'}), 500

@meetings_bp.route('/<int:id>/participants/<int:participant_id>/reject', methods=['POST'])
@token_required
def reject_participant(current_user, id, participant_id):
    try:
        meeting = Meeting.query.get(id)
        
        if not meeting:
            return jsonify({'error': 'Meeting not found'}), 404
            
        # Check if user has permission to reject participants
        if meeting.created_by != current_user.id and not MeetingCoHost.query.filter_by(
            meeting_id=id,
            user_id=current_user.id
        ).first():
            return jsonify({'error': 'Access denied'}), 403
            
        participant = MeetingParticipant.query.get(participant_id)
        
        if not participant or participant.meeting_id != id:
            return jsonify({'error': 'Participant not found'}), 404
            
        if participant.status != 'pending':
            return jsonify({'error': 'Participant is not in waiting room'}), 400
            
        participant.status = 'declined'
        
        # Log the action
        audit_log = MeetingAuditLog(
            meeting_id=id,
            user_id=current_user.id,
            action='rejected_participant',
            details={'participant_id': participant_id}
        )
        db.session.add(audit_log)
        
        db.session.commit()
        
        return jsonify({'message': 'Participant rejected successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Server error occurred while rejecting participant'}), 500 
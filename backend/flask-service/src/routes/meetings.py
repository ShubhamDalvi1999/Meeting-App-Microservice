from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
import bleach
import json
import time
from meeting_shared.middleware.auth import jwt_required
from meeting_shared.middleware.error_handler import error_handler, APIError
from meeting_shared.middleware.validation import validate_schema
from meeting_shared.schemas.base import ErrorResponse, SuccessResponse
from ..schemas.meeting import MeetingCreate, MeetingResponse, MeetingUpdate
from ..models import db, User, Meeting, MeetingParticipant, MeetingCoHost, MeetingAuditLog
from ..utils.auth_integration import enhanced_token_required

meetings_bp = Blueprint('meetings', __name__)

def get_cache_client():
    """Get Redis client from app extensions"""
    return current_app.extensions.get('redis')

def get_cached_meetings(cache_key):
    """Get meetings from cache if available"""
    redis_client = get_cache_client()
    if not redis_client:
        return None
        
    cached = redis_client.get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except Exception as e:
            current_app.logger.error(f"Error parsing cached meetings: {e}")
    return None

def cache_meetings(cache_key, meetings, expiry=300):
    """Cache meetings in Redis"""
    redis_client = get_cache_client()
    if not redis_client:
        return
        
    try:
        redis_client.setex(cache_key, expiry, json.dumps(meetings))
    except Exception as e:
        current_app.logger.error(f"Error caching meetings: {e}")

@meetings_bp.route('/create', methods=['POST'])
@enhanced_token_required
@error_handler
def create_meeting(current_user):
    """Create a new meeting."""
    data = request.get_json()
    
    if not data:
        raise APIError('No data provided', 400)
        
    required_fields = ['title', 'description', 'start_time', 'end_time']
    if not all(field in data for field in required_fields):
        raise APIError('Missing required fields', 400, 
                       {'required': required_fields})
        
    # Validate title and description
    title = bleach.clean(data['title'].strip())
    description = bleach.clean(data['description'].strip())
    
    if not title:
        raise APIError('Meeting title cannot be empty', 400)
        
    if len(title) > 200:
        raise APIError('Meeting title too long (max 200 characters)', 400)
        
    if len(description) > 2000:
        raise APIError('Meeting description too long (max 2000 characters)', 400)

    try:
        start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        
        if not start_time.tzinfo or not end_time.tzinfo:
            raise APIError('Timezone information is required', 400)
            
    except ValueError:
        raise APIError('Invalid datetime format. Please use ISO format', 400)

    current_time = datetime.now(timezone.utc)
    
    # Enhanced time validations
    if start_time < current_time:
        raise APIError('Meeting cannot start in the past', 400)
        
    if start_time >= end_time:
        raise APIError('Start time must be before end time', 400)
        
    # Validate reasonable time ranges
    duration = end_time - start_time
    if duration.total_seconds() < 300:  # 5 minutes minimum
        raise APIError('Meeting must be at least 5 minutes long', 400)
        
    if duration.total_seconds() > 86400:  # 24 hours maximum
        raise APIError('Meeting cannot be longer than 24 hours', 400)
        
    # Check if start time is too far in the future
    if (start_time - current_time).days > 365:
        raise APIError('Cannot schedule meetings more than 1 year in advance', 400)
        
    # Validate meeting type and settings
    meeting_type = data.get('meeting_type', 'regular')
    if meeting_type not in ['regular', 'recurring', 'private']:
        raise APIError('Invalid meeting type', 400, {'valid_types': ['regular', 'recurring', 'private']})
        
    max_participants = data.get('max_participants')
    if max_participants is not None:
        if not isinstance(max_participants, int) or max_participants <= 0:
            raise APIError('Invalid maximum participants value', 400)
            
    requires_approval = data.get('requires_approval', False)
    is_recorded = data.get('is_recorded', False)
    
    # Handle recurring meeting pattern
    recurring_pattern = None
    if meeting_type == 'recurring':
        recurring_pattern = data.get('recurring_pattern')
        if not recurring_pattern or recurring_pattern not in ['daily', 'weekly', 'monthly', 'custom']:
            raise APIError('Invalid recurring pattern for recurring meeting', 400, 
                           {'valid_patterns': ['daily', 'weekly', 'monthly', 'custom']})
    
    # Check for overlapping meetings for the user
    user_meetings = Meeting.query.filter(
        Meeting.created_by == current_user.id,
        Meeting.ended_at.is_(None),
        Meeting.end_time > start_time,
        Meeting.start_time < end_time
    ).first()
    
    if user_meetings:
        raise APIError('You have another meeting scheduled during this time', 400)
        
    # Check total number of active meetings for user
    active_meetings_count = Meeting.query.filter(
        Meeting.created_by == current_user.id,
        Meeting.ended_at.is_(None)
    ).count()
    
    if active_meetings_count >= 50:
        raise APIError('You have reached the maximum limit of active meetings', 400)
    
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
    
    # Invalidate cache for this user's meetings
    redis_client = get_cache_client()
    if redis_client:
        cache_key = f"meetings:user:{current_user.id}"
        redis_client.delete(cache_key)
    
    db.session.commit()
    
    response = MeetingResponse.from_orm(meeting)
    return jsonify(response.model_dump()), 201

@meetings_bp.route('/join/<int:id>', methods=['GET'])
@enhanced_token_required
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
        current_time = datetime.now(timezone.utc)
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
@enhanced_token_required
@error_handler
def list_meetings(current_user):
    """Get list of meetings for the current user with caching."""
    # Get query parameters for filtering
    active_only = request.args.get('active_only', type=lambda v: v.lower() == 'true', default=True)
    force_refresh = request.args.get('refresh', type=lambda v: v.lower() == 'true', default=False)
    
    # Generate cache key based on user and filters
    cache_key = f"meetings:user:{current_user.id}:active:{active_only}"
    
    # Try to get from cache if not forcing refresh
    if not force_refresh:
        cached_meetings = get_cached_meetings(cache_key)
        if cached_meetings is not None:
            return jsonify(cached_meetings)
    
    # Track performance
    start_time = time.time()
    
    # First, get meetings where user is creator
    creator_meetings = Meeting.query.filter(Meeting.created_by == current_user.id)
    if active_only:
        creator_meetings = creator_meetings.filter(Meeting.ended_at.is_(None))
    creator_meetings = creator_meetings.all()

    # Then, get meetings where user is participant
    participant_meetings = Meeting.query.join(MeetingParticipant).filter(
        MeetingParticipant.user_id == current_user.id
    )
    if active_only:
        participant_meetings = participant_meetings.filter(Meeting.ended_at.is_(None))
    participant_meetings = participant_meetings.all()

    # Combine and sort meetings
    all_meetings = sorted(
        set(creator_meetings + participant_meetings),
        key=lambda m: m.start_time,
        reverse=True
    )
    
    # Convert to response format
    response_meetings = [MeetingResponse.from_orm(meeting).model_dump() for meeting in all_meetings]
    
    # Calculate query time for optimization metrics
    query_time = time.time() - start_time
    
    # Cache the results (only if query is slow enough to warrant caching)
    if query_time > 0.1:  # Only cache if query takes more than 100ms
        cache_meetings(cache_key, response_meetings)
    
    # Log performance metrics
    current_app.logger.debug(f"Meeting list query took {query_time:.3f}s for user {current_user.id}")
    
    return jsonify(response_meetings)

@meetings_bp.route('/<int:id>', methods=['GET'])
@enhanced_token_required
@error_handler
def get_meeting(current_user, id):
    """Get a specific meeting by ID."""
    meeting = Meeting.query.get(id)
    
    if not meeting:
        raise APIError('Meeting not found', 404)
        
    # Check if user has access to the meeting
    if meeting.created_by != current_user.id and current_user.id not in [p.user_id for p in meeting.participants]:
        raise APIError('Access denied', 403)
        
    response = MeetingResponse.from_orm(meeting)
    return jsonify(response.model_dump())

@meetings_bp.route('/<int:id>', methods=['DELETE'])
@enhanced_token_required
@error_handler
def delete_meeting(current_user, id):
    """Delete/cancel a meeting."""
    meeting = Meeting.query.get(id)
    
    if not meeting:
        raise APIError('Meeting not found', 404)
        
    # Only the creator can delete a meeting
    if meeting.created_by != current_user.id:
        raise APIError('You do not have permission to delete this meeting', 403)
        
    # If meeting has started, mark as ended instead of deleting
    current_time = datetime.now(timezone.utc)
    if meeting.start_time <= current_time:
        meeting.ended_at = current_time
        
        # Log early termination
        audit_log = MeetingAuditLog(
            meeting_id=meeting.id,
            user_id=current_user.id,
            action='ended_early',
            details={"ended_at": current_time.isoformat()}
        )
    else:
        # Log cancellation
        audit_log = MeetingAuditLog(
            meeting_id=meeting.id,
            user_id=current_user.id,
            action='cancelled',
            details={"cancelled_at": current_time.isoformat()}
        )
        
        # Mark as cancelled
        meeting.is_cancelled = True
        meeting.cancelled_at = current_time
        
    db.session.add(audit_log)
    
    # Invalidate cache for this user's meetings and other participants
    redis_client = get_cache_client()
    if redis_client:
        # Invalidate creator's cache
        redis_client.delete(f"meetings:user:{meeting.created_by}")
        redis_client.delete(f"meetings:user:{meeting.created_by}:active:true")
        redis_client.delete(f"meetings:user:{meeting.created_by}:active:false")
        
        # Invalidate participant caches
        for participant in meeting.participants:
            redis_client.delete(f"meetings:user:{participant.user_id}")
            redis_client.delete(f"meetings:user:{participant.user_id}:active:true")
            redis_client.delete(f"meetings:user:{participant.user_id}:active:false")
    
    db.session.commit()
    
    return jsonify(SuccessResponse(
        message="Meeting cancelled successfully" if meeting.is_cancelled else "Meeting ended successfully"
    ).model_dump())

@meetings_bp.route('/stats', methods=['GET'])
@enhanced_token_required
@error_handler
def get_meeting_stats(current_user):
    """Get meeting statistics for the current user."""
    # Try to get from cache first
    cache_key = f"meeting_stats:user:{current_user.id}"
    cached_stats = get_cached_meetings(cache_key)
    if cached_stats is not None:
        return jsonify(cached_stats)
        
    # Calculate stats
    current_time = datetime.now(timezone.utc)
    
    # Active meetings where user is creator
    active_hosted = Meeting.query.filter(
        Meeting.created_by == current_user.id,
        Meeting.ended_at.is_(None),
        Meeting.is_cancelled == False
    ).count()
    
    # Upcoming meetings where user is creator
    upcoming_hosted = Meeting.query.filter(
        Meeting.created_by == current_user.id,
        Meeting.start_time > current_time,
        Meeting.is_cancelled == False
    ).count()
    
    # Active meetings where user is participant
    active_participating = db.session.query(Meeting).join(MeetingParticipant).filter(
        MeetingParticipant.user_id == current_user.id,
        Meeting.ended_at.is_(None),
        Meeting.is_cancelled == False
    ).count()
    
    # Upcoming meetings where user is participant
    upcoming_participating = db.session.query(Meeting).join(MeetingParticipant).filter(
        MeetingParticipant.user_id == current_user.id,
        Meeting.start_time > current_time,
        Meeting.is_cancelled == False
    ).count()
    
    # All past meetings as host
    past_hosted = Meeting.query.filter(
        Meeting.created_by == current_user.id,
        Meeting.ended_at.isnot(None)
    ).count()
    
    # All past meetings as participant
    past_participating = db.session.query(Meeting).join(MeetingParticipant).filter(
        MeetingParticipant.user_id == current_user.id,
        Meeting.ended_at.isnot(None)
    ).count()
    
    # Calculate total meeting hours
    total_hours_query = db.session.query(
        db.func.sum(db.func.extract('epoch', Meeting.end_time - Meeting.start_time) / 3600)
    ).filter(
        Meeting.created_by == current_user.id,
        Meeting.ended_at.isnot(None)
    ).scalar()
    
    total_meeting_hours = round(float(total_hours_query or 0), 1)
    
    stats = {
        "active_hosted": active_hosted,
        "upcoming_hosted": upcoming_hosted,
        "active_participating": active_participating,
        "upcoming_participating": upcoming_participating,
        "past_hosted": past_hosted,
        "past_participating": past_participating,
        "total_meeting_hours": total_meeting_hours,
        "total_meetings": past_hosted + active_hosted
    }
    
    # Cache for 10 minutes
    cache_meetings(cache_key, stats, 600)
    
    return jsonify(stats) 
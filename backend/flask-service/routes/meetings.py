from flask import Blueprint, request, jsonify
from app import db
from models.meeting import Meeting
from routes.auth import token_required

meetings_bp = Blueprint('meetings', __name__)

@meetings_bp.route('/create', methods=['POST'])
@token_required
def create_meeting(current_user):
    data = request.get_json()
    
    if 'title' not in data:
        return jsonify({'message': 'Meeting title is required'}), 400
    
    meeting = Meeting(
        title=data['title'],
        host_id=current_user.id
    )
    
    db.session.add(meeting)
    db.session.commit()
    
    return jsonify(meeting.to_dict()), 201

@meetings_bp.route('/join/<code>', methods=['GET'])
@token_required
def join_meeting(current_user, code):
    meeting = Meeting.query.filter_by(code=code, is_active=True).first()
    
    if not meeting:
        return jsonify({'message': 'Meeting not found or inactive'}), 404
    
    return jsonify(meeting.to_dict()), 200

@meetings_bp.route('/end/<code>', methods=['POST'])
@token_required
def end_meeting(current_user, code):
    meeting = Meeting.query.filter_by(code=code, host_id=current_user.id).first()
    
    if not meeting:
        return jsonify({'message': 'Meeting not found'}), 404
    
    if not meeting.is_active:
        return jsonify({'message': 'Meeting already ended'}), 400
    
    meeting.is_active = False
    db.session.commit()
    
    return jsonify(meeting.to_dict()), 200

@meetings_bp.route('/list', methods=['GET'])
@token_required
def list_meetings(current_user):
    meetings = Meeting.query.filter_by(host_id=current_user.id).order_by(Meeting.created_at.desc()).all()
    return jsonify([meeting.to_dict() for meeting in meetings]), 200 
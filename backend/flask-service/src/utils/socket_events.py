from flask_socketio import emit, join_room, leave_room
from functools import wraps
import jwt
import os

def socket_auth_required(f):
    @wraps(f)
    def decorated(data, *args, **kwargs):
        token = data.get('token')
        
        if not token:
            return emit('error', {'message': 'Token is missing'})
            
        try:
            token_data = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=['HS256'])
            data['user_id'] = token_data['user_id']
        except:
            return emit('error', {'message': 'Invalid token'})
            
        return f(data, *args, **kwargs)
        
    return decorated

def register_socket_events(socketio):
    @socketio.on('join')
    @socket_auth_required
    def handle_join(data):
        room = data.get('meeting_code')
        if room:
            join_room(room)
            emit('user_joined', {
                'user_id': data['user_id']
            }, room=room)

    @socketio.on('leave')
    @socket_auth_required
    def handle_leave(data):
        room = data.get('meeting_code')
        if room:
            leave_room(room)
            emit('user_left', {
                'user_id': data['user_id']
            }, room=room)

    @socketio.on('offer')
    @socket_auth_required
    def handle_offer(data):
        target_user = data.get('target_user')
        if target_user:
            emit('offer', {
                'sdp': data['sdp'],
                'user_id': data['user_id']
            }, room=target_user)

    @socketio.on('answer')
    @socket_auth_required
    def handle_answer(data):
        target_user = data.get('target_user')
        if target_user:
            emit('answer', {
                'sdp': data['sdp'],
                'user_id': data['user_id']
            }, room=target_user)

    @socketio.on('ice_candidate')
    @socket_auth_required
    def handle_ice_candidate(data):
        target_user = data.get('target_user')
        if target_user:
            emit('ice_candidate', {
                'candidate': data['candidate'],
                'user_id': data['user_id']
            }, room=target_user)

    @socketio.on('chat_message')
    @socket_auth_required
    def handle_chat_message(data):
        room = data.get('meeting_code')
        if room:
            emit('chat_message', {
                'user_id': data['user_id'],
                'message': data['message'],
                'timestamp': data['timestamp']
            }, room=room) 
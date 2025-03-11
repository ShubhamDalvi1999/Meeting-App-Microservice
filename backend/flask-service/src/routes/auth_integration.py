from flask import Blueprint, request, jsonify, current_app
from functools import wraps
from ..utils.auth_integration import AuthIntegration
from meeting_shared.middleware.auth import service_auth_required
from meeting_shared.middleware.validation import validate_schema
from meeting_shared.schemas.base import ErrorResponse, SuccessResponse
from meeting_shared.database import transaction_context
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('auth_integration', __name__)

def require_service_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        service_key = request.headers.get('X-Service-Key')
        if not service_key or service_key != current_app.config['AUTH_SERVICE_KEY']:
            return jsonify({'error': 'Invalid service key'}), 403
        return f(*args, **kwargs)
    return decorated

@bp.route('/auth/validate-token', methods=['POST'])
@service_auth_required
def validate_token():
    """Validate JWT token"""
    try:
        data = request.get_json()
        token = data.get('token')
        if not token:
            return jsonify(ErrorResponse(
                error="Validation Error",
                message="Token is required"
            ).model_dump()), 400

        auth_integration = AuthIntegration()
        payload = auth_integration.validate_token(token)
        
        if payload:
            return jsonify(SuccessResponse(data=payload).model_dump())
        return jsonify(ErrorResponse(
            error="Authentication Error",
            message="Invalid token"
        ).model_dump()), 401
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        return jsonify(ErrorResponse(
            error="Internal Server Error",
            message="Failed to validate token"
        ).model_dump()), 500

@bp.route('/auth/sync-session', methods=['POST'])
@service_auth_required
def sync_session():
    """Synchronize session data from auth service"""
    try:
        data = request.get_json()
        auth_integration = AuthIntegration()
        
        with transaction_context() as session:
            if auth_integration.sync_user_session(data):
                return jsonify(SuccessResponse(
                    message="Session synchronized successfully"
                ).model_dump())
            
            return jsonify(ErrorResponse(
                error="Sync Error",
                message="Failed to sync session"
            ).model_dump()), 400
            
    except Exception as e:
        logger.error(f"Error syncing session: {str(e)}")
        return jsonify(ErrorResponse(
            error="Internal Server Error",
            message="Failed to process sync request"
        ).model_dump()), 500

@bp.route('/auth/sync-user', methods=['POST'])
@service_auth_required
def sync_user():
    """Synchronize user data from auth service"""
    try:
        data = request.get_json()
        auth_integration = AuthIntegration()
        
        with transaction_context() as session:
            if auth_integration.sync_user_data(data):
                return jsonify(SuccessResponse(
                    message="User data synchronized successfully"
                ).model_dump())
            return jsonify(ErrorResponse(
                error="Sync Error",
                message="Failed to sync user data"
            ).model_dump()), 400
    except Exception as e:
        logger.error(f"Error syncing user data: {str(e)}")
        return jsonify(ErrorResponse(
            error="Internal Server Error",
            message="Failed to sync user data"
        ).model_dump()), 500

@bp.route('/auth/revoke-user-sessions', methods=['POST'])
@service_auth_required
def revoke_sessions():
    """Handle session revocation from auth service"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        reason = data.get('reason')
        
        if not user_id:
            return jsonify(ErrorResponse(
                error="Validation Error",
                message="User ID is required"
            ).model_dump()), 400

        auth_integration = AuthIntegration()
        with transaction_context() as session:
            if auth_integration.revoke_user_sessions(user_id, reason):
                return jsonify(SuccessResponse(
                    message="User sessions revoked successfully"
                ).model_dump())
            return jsonify(ErrorResponse(
                error="Revocation Error",
                message="Failed to revoke sessions"
            ).model_dump()), 400
    except Exception as e:
        logger.error(f"Error revoking sessions: {str(e)}")
        return jsonify(ErrorResponse(
            error="Internal Server Error",
            message="Failed to revoke sessions"
        ).model_dump()), 500 
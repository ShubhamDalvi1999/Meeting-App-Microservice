from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import bcrypt
import jwt
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import re
import secrets
from ..models.auth import AuthUser, PasswordResetToken, UserSession, EmailVerification
from shared.database import db, transaction
from shared.middleware.validation import validate_schema
from shared.middleware.rate_limiter import rate_limit
from shared.middleware.auth import jwt_required
from shared.schemas.base import ErrorResponse, SuccessResponse
from ..schemas.auth import (
    AuthUserCreate, AuthUserLogin, GoogleLogin, PasswordReset,
    PasswordResetConfirm, SessionCreate, TokenRefresh, SessionRevoke
)
from ..utils.email_service import send_verification_email
from ..utils.auth import get_current_user, get_current_session
import logging

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

def validate_password(password):
    """Validate password strength"""
    if len(password) < 12:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    if not re.search(r'[@$!%*?&]', password):
        return False
    return True

def generate_verification_token():
    """Generate a secure verification token"""
    return secrets.token_urlsafe(32)

@auth_bp.route('/register', methods=['POST'])
@rate_limit(requests=5, window=3600)  # 5 registrations per hour
@validate_schema(AuthUserCreate)
def register(data: AuthUserCreate):
    """Register a new user"""
    try:
        with transaction():
            # Check if user already exists
            if AuthUser.query.filter_by(email=data.email.lower()).first():
                return jsonify(ErrorResponse(
                    error="Registration Error",
                    message="Email already registered"
                ).model_dump()), 409

            # Create user
            user = AuthUser.from_schema(data)
            db.session.add(user)
            db.session.flush()  # Get user ID without committing

            # Create verification token
            verification = user.create_verification_token()
            db.session.add(verification)

            # Send verification email
            if not send_verification_email(user.email, verification.token):
                raise Exception("Failed to send verification email")

        return jsonify(SuccessResponse(
            message="Registration successful",
            data={"user": user.to_schema().model_dump()}
        ).model_dump()), 201

    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify(ErrorResponse(
            error="Registration Error",
            message="Failed to register user"
        ).model_dump()), 500

@auth_bp.route('/verify-email/<token>', methods=['GET'])
@rate_limit(requests=10, window=3600)  # 10 verification attempts per hour
@with_transaction
def verify_email(token):
    verification = EmailVerification.query.filter_by(
        token=token,
        is_used=False
    ).first()

    if not verification or verification.expires_at < datetime.utcnow():
        return jsonify({'error': 'Invalid or expired verification token'}), 400

    user = verification.user
    user.is_email_verified = True
    verification.is_used = True

    return jsonify({
        'message': 'Email verified successfully',
        'user': user.to_dict()
    }), 200

@auth_bp.route('/resend-verification', methods=['POST'])
@rate_limit(requests=3, window=3600)  # 3 resend attempts per hour
def resend_verification():
    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    user = AuthUser.query.filter_by(email=email.lower()).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user.is_email_verified:
        return jsonify({'error': 'Email is already verified'}), 400

    # Create new verification token
    token = generate_verification_token()
    verification = EmailVerification(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.session.add(verification)
    db.session.commit()

    # Send verification email
    if not send_verification_email(user.email, token):
        return jsonify({'error': 'Failed to send verification email'}), 500

    return jsonify({
        'message': 'Verification email sent successfully'
    }), 200

@auth_bp.route('/login', methods=['POST'])
@rate_limit(requests=10, window=300)  # 10 login attempts per 5 minutes
@validate_schema(AuthUserLogin)
def login(data: AuthUserLogin):
    """User login"""
    try:
        user = AuthUser.query.filter_by(email=data.email.lower()).first()
        if not user or not user.check_password(data.password):
            return jsonify(ErrorResponse(
                error="Authentication Error",
                message="Invalid email or password"
            ).model_dump()), 401

        if user.is_locked():
            return jsonify(ErrorResponse(
                error="Authentication Error",
                message="Account is locked. Please try again later"
            ).model_dump()), 403

        with transaction():
            # Create session
            session = user.create_session(data.device_info)
            
            # Update user login info
            user.last_login = datetime.utcnow()
            user.failed_login_attempts = 0
            
            return jsonify(SuccessResponse(
                message="Login successful",
                data={
                    "token": session.token,
                    "refresh_token": session.refresh_token,
                    "user": user.to_schema().model_dump()
                }
            ).model_dump())

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify(ErrorResponse(
            error="Authentication Error",
            message="Login failed"
        ).model_dump()), 500

@auth_bp.route('/google/login', methods=['POST'])
@validate_schema(GoogleLogin)
def google_login(data: GoogleLogin):
    """Handle Google OAuth login"""
    try:
        # Verify Google token
        idinfo = id_token.verify_oauth2_token(
            data.token,
            google_requests.Request(),
            current_app.config['GOOGLE_CLIENT_ID']
        )

        email = idinfo['email']
        
        with transaction():
            # Check if user exists
            user = AuthUser.query.filter_by(email=email).first()
            
            if not user:
                # Create new user
                user = AuthUser(
                    email=email,
                    is_google_user=True,
                    is_email_verified=True,
                    first_name=idinfo.get('given_name'),
                    last_name=idinfo.get('family_name'),
                    profile_picture=idinfo.get('picture'),
                    google_id=idinfo['sub']
                )
                db.session.add(user)
                db.session.flush()
            
            # Update Google info if needed
            if user.google_id != idinfo['sub']:
                user.google_id = idinfo['sub']
                user.is_google_user = True
            
            # Create session
            session = user.create_session(data.device_info)
            user.last_login = datetime.utcnow()
            
            return jsonify(SuccessResponse(
                message="Google login successful",
                data={
                    "token": session.token,
                    "refresh_token": session.refresh_token,
                    "user": user.to_schema().model_dump()
                }
            ).model_dump())

    except ValueError as e:
        # Invalid token
        logger.error(f"Invalid Google token: {str(e)}")
        return jsonify(ErrorResponse(
            error="Authentication Error",
            message="Invalid Google token"
        ).model_dump()), 401
    except Exception as e:
        logger.error(f"Google login error: {str(e)}")
        return jsonify(ErrorResponse(
            error="Authentication Error",
            message="Google login failed"
        ).model_dump()), 500

@auth_bp.route('/reset-password', methods=['POST'])
@rate_limit(requests=3, window=3600)  # 3 reset attempts per hour
@validate_schema(PasswordReset)
def reset_password(data: PasswordReset):
    """Initiate password reset"""
    try:
        user = AuthUser.query.filter_by(email=data.email.lower()).first()
        if not user:
            # Return success even if user doesn't exist (security)
            return jsonify(SuccessResponse(
                message="If your email is registered, you will receive reset instructions"
            ).model_dump())

        with transaction():
            # Create reset token
            token = PasswordResetToken(
                user_id=user.id,
                token=secrets.token_urlsafe(32),
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db.session.add(token)
            
            # Send reset email (implement this)
            # send_password_reset_email(user.email, token.token)
            
            return jsonify(SuccessResponse(
                message="If your email is registered, you will receive reset instructions"
            ).model_dump())

    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        return jsonify(ErrorResponse(
            error="Reset Error",
            message="Failed to process password reset"
        ).model_dump()), 500

@auth_bp.route('/reset-password/confirm', methods=['POST'])
@validate_schema(PasswordResetConfirm)
def confirm_reset_password(data: PasswordResetConfirm):
    """Confirm password reset"""
    try:
        # Find valid token
        token = PasswordResetToken.query.filter_by(
            token=data.token,
            used=False
        ).filter(PasswordResetToken.expires_at > datetime.utcnow()).first()

        if not token:
            return jsonify(ErrorResponse(
                error="Reset Error",
                message="Invalid or expired token"
            ).model_dump()), 400

        with transaction():
            # Update password
            user = token.user
            user.set_password(data.new_password)
            
            # Invalidate token
            token.used = True
            
            # Revoke all sessions
            UserSession.query.filter_by(user_id=user.id).update({
                'revoked': True,
                'revoked_at': datetime.utcnow(),
                'revocation_reason': 'Password reset'
            })
            
            return jsonify(SuccessResponse(
                message="Password has been reset successfully"
            ).model_dump())

    except Exception as e:
        logger.error(f"Password reset confirmation error: {str(e)}")
        return jsonify(ErrorResponse(
            error="Reset Error",
            message="Failed to reset password"
        ).model_dump()), 500

@auth_bp.route('/refresh-token', methods=['POST'])
@validate_schema(TokenRefresh)
def refresh_token(data: TokenRefresh):
    """Refresh access token using refresh token"""
    try:
        # Find valid session by refresh token
        session = UserSession.query.filter_by(
            refresh_token=data.refresh_token,
            revoked=False
        ).filter(UserSession.refresh_token_expires_at > datetime.utcnow()).first()

        if not session:
            return jsonify(ErrorResponse(
                error="Authentication Error",
                message="Invalid or expired refresh token"
            ).model_dump()), 401

        with transaction():
            # Create new session
            new_session = session.refresh()
            
            return jsonify(SuccessResponse(
                message="Token refreshed successfully",
                data={
                    "token": new_session.token,
                    "refresh_token": new_session.refresh_token
                }
            ).model_dump())

    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return jsonify(ErrorResponse(
            error="Authentication Error",
            message="Failed to refresh token"
        ).model_dump()), 500

@auth_bp.route('/sessions', methods=['GET'])
@jwt_required
def list_sessions():
    """List all active sessions for the current user"""
    try:
        current_user = get_current_user()
        sessions = UserSession.query.filter_by(
            user_id=current_user.id,
            revoked=False
        ).filter(UserSession.expires_at > datetime.utcnow()).all()
        
        return jsonify(SuccessResponse(
            message="Sessions retrieved successfully",
            data={
                "sessions": [session.to_schema().model_dump() for session in sessions],
                "total_count": len(sessions)
            }
        ).model_dump())

    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        return jsonify(ErrorResponse(
            error="Session Error",
            message="Failed to list sessions"
        ).model_dump()), 500

@auth_bp.route('/sessions/<int:session_id>/revoke', methods=['POST'])
@jwt_required
@validate_schema(SessionRevoke)
def revoke_session(session_id: int, data: SessionRevoke):
    """Revoke a specific session"""
    try:
        current_user = get_current_user()
        current_session = get_current_session()
        
        # Find session
        session = UserSession.query.filter_by(
            id=session_id,
            user_id=current_user.id,
            revoked=False
        ).first()
        
        if not session:
            return jsonify(ErrorResponse(
                error="Session Error",
                message="Session not found"
            ).model_dump()), 404
            
        with transaction():
            session.revoke(reason=data.reason or "User initiated revocation")
            
            return jsonify(SuccessResponse(
                message="Session revoked successfully"
            ).model_dump())

    except Exception as e:
        logger.error(f"Error revoking session: {str(e)}")
        return jsonify(ErrorResponse(
            error="Session Error",
            message="Failed to revoke session"
        ).model_dump()), 500

@auth_bp.route('/sessions/revoke-all', methods=['POST'])
@jwt_required
def revoke_all_sessions():
    """Revoke all sessions except the current one"""
    try:
        current_user = get_current_user()
        current_session = get_current_session()
        
        with transaction():
            # Revoke all other sessions
            UserSession.query.filter(
                UserSession.user_id == current_user.id,
                UserSession.id != current_session.id,
                UserSession.revoked == False
            ).update({
                'revoked': True,
                'revoked_at': datetime.utcnow(),
                'revocation_reason': 'User revoked all sessions'
            })
            
            return jsonify(SuccessResponse(
                message="All other sessions revoked successfully"
            ).model_dump())

    except Exception as e:
        logger.error(f"Error revoking all sessions: {str(e)}")
        return jsonify(ErrorResponse(
            error="Session Error",
            message="Failed to revoke sessions"
        ).model_dump()), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required
def logout():
    """Log out user by revoking current session"""
    try:
        current_session = get_current_session()
        
        with transaction():
            current_session.revoke(reason="User logout")
            
            return jsonify(SuccessResponse(
                message="Logged out successfully"
            ).model_dump())

    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify(ErrorResponse(
            error="Logout Error",
            message="Failed to logout"
        ).model_dump()), 500 
from typing import Optional, Dict, Any, Tuple
from flask import current_app, request, g
from meeting_shared.database import db, transaction_context
from meeting_shared.middleware.auth import jwt_required
from meeting_shared.schemas.base import ErrorResponse
from ..models.user import User
import jwt
import logging
import requests
import json
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)

class AuthIntegration:
    def __init__(self):
        self.jwt_secret = current_app.config['JWT_SECRET_KEY']
        self.algorithm = 'HS256'
        self.auth_service_url = current_app.config.get('AUTH_SERVICE_URL', 'http://auth-service:5001')
        self.service_key = current_app.config.get('SERVICE_KEY')
        self.token_cache = {}  # Simple in-memory cache for token validation results
        self.token_cache_expiry = {}  # Expiry times for cache entries
        self.cache_ttl = 300  # 5 minutes cache TTL

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return payload if valid"""
        try:
            # Check cache first to avoid repeated decoding
            if token in self.token_cache:
                # Check if cache entry is still valid
                if datetime.now().timestamp() < self.token_cache_expiry.get(token, 0):
                    return self.token_cache[token]
                else:
                    # Remove expired entry
                    self.token_cache.pop(token, None)
                    self.token_cache_expiry.pop(token, None)
            
            # First try local validation
            try:
                payload = jwt.decode(token, self.jwt_secret, algorithms=[self.algorithm])
                
                # Check if the user exists in our database
                user = User.query.get(payload.get('user_id'))
                if not user:
                    logger.warning(f"User {payload.get('user_id')} not found in database during token validation")
                    return self._verify_with_auth_service(token)
                
                # Cache the successful result
                self.token_cache[token] = payload
                self.token_cache_expiry[token] = datetime.now().timestamp() + self.cache_ttl
                return payload
            except jwt.InvalidTokenError as e:
                # If local validation fails, verify with auth service
                logger.info(f"Local token validation failed: {str(e)}, trying auth service")
                return self._verify_with_auth_service(token)
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return None

    def _verify_with_auth_service(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify token with auth service"""
        try:
            headers = {'X-Service-Key': self.service_key}
            response = requests.post(
                f"{self.auth_service_url}/api/auth/validate-token",
                json={"token": token},
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                payload = response.json().get('data', {})
                
                # Cache the successful result
                self.token_cache[token] = payload
                self.token_cache_expiry[token] = datetime.now().timestamp() + self.cache_ttl
                return payload
            else:
                logger.warning(f"Auth service rejected token: {response.status_code}, {response.text}")
                return None
        except requests.RequestException as e:
            logger.error(f"Error connecting to auth service: {str(e)}")
            # Fall back to local validation as a last resort
            try:
                return jwt.decode(token, self.jwt_secret, algorithms=[self.algorithm])
            except:
                return None

    def get_user_from_token(self, token: str) -> Tuple[Optional[User], Optional[str]]:
        """
        Get user from token and handle error messages
        Returns (user, error_message)
        """
        try:
            payload = self.validate_token(token)
            if not payload:
                return None, "Invalid or expired token"
            
            user_id = payload.get('user_id')
            if not user_id:
                return None, "Token missing user ID"
            
            user = User.query.get(user_id)
            if not user:
                return None, "User not found"
            
            if not user.is_active:
                return None, "Account is inactive"
            
            return user, None
        except Exception as e:
            logger.error(f"Error getting user from token: {str(e)}")
            return None, f"Authentication error: {str(e)}"

    def sync_user_session(self, data: Dict[str, Any]) -> bool:
        """
        Synchronize user session data from auth service
        """
        try:
            with transaction_context() as session:
                user_id = data.get('user_id')
                if not user_id:
                    return True  # Skip for cleanup notifications
                
                user = User.query.get(user_id)
                if not user:
                    logger.warning(f"User {user_id} not found during session sync")
                    return False

                # Update user's session state
                session_data = data.get('session_data', {})
                user.last_login_at = datetime.fromisoformat(session_data.get('expires_at')) if session_data.get('expires_at') else None
                user.is_active = session_data.get('is_active', True)
                
                # Clear any cached tokens for this user
                self._clear_user_token_cache(user_id)
                
                return True
                
        except Exception as e:
            logger.error(f"Error syncing user session: {str(e)}")
            return False
            
    def _clear_user_token_cache(self, user_id: int) -> None:
        """Clear cached tokens for a specific user"""
        try:
            # Find all tokens in cache that belong to this user
            tokens_to_remove = []
            for token, payload in self.token_cache.items():
                if payload.get('user_id') == user_id:
                    tokens_to_remove.append(token)
            
            # Remove tokens from cache
            for token in tokens_to_remove:
                self.token_cache.pop(token, None)
                self.token_cache_expiry.pop(token, None)
                
            logger.debug(f"Cleared {len(tokens_to_remove)} cached tokens for user {user_id}")
        except Exception as e:
            logger.error(f"Error clearing user token cache: {str(e)}")
            
    def cleanup_token_cache(self) -> int:
        """
        Clean up expired token cache entries
        Returns number of entries removed
        """
        try:
            now = datetime.now().timestamp()
            tokens_to_remove = [
                token for token, expiry in self.token_cache_expiry.items()
                if expiry < now
            ]
            
            for token in tokens_to_remove:
                self.token_cache.pop(token, None)
                self.token_cache_expiry.pop(token, None)
                
            return len(tokens_to_remove)
        except Exception as e:
            logger.error(f"Error cleaning up token cache: {str(e)}")
            return 0

def enhanced_token_required(f):
    """
    Enhanced decorator to require JWT token for route access
    Uses AuthIntegration for validation with caching and auth service fallback
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return ErrorResponse(
                error="Authentication Error",
                message="Missing or invalid Authorization header"
            ).to_response(401)
        
        token = auth_header.split(' ')[1]
        
        # Get auth integration instance
        auth_integration = AuthIntegration()
        
        # Try to get user from token
        user, error = auth_integration.get_user_from_token(token)
        if not user:
            return ErrorResponse(
                error="Authentication Error",
                message=error or "Invalid token"
            ).to_response(401)
        
        # Store in flask g object for route access
        g.current_user = user
        g.current_token = token
        
        return f(user, *args, **kwargs)
    
    return decorated

    def sync_user_data(self, data: Dict[str, Any]) -> bool:
        """
        Synchronize user data from auth service
        """
        try:
            with transaction_context() as session:
                user_id = data.get('id')
                if not user_id:
                    return False

                user = User.query.get(user_id)
                if not user:
                    # Create user if doesn't exist
                    user = User(
                        id=user_id,
                        email=data['email'],
                        name=f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
                        is_active=data['is_active'],
                        is_email_verified=data['is_email_verified']
                    )
                    session.add(user)
                else:
                    # Update existing user
                    user.email = data['email']
                    user.name = f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
                    user.is_active = data['is_active']
                    user.is_email_verified = data['is_email_verified']

                return True
        except Exception as e:
            logger.error(f"Error syncing user data: {str(e)}")
            return False

    def revoke_user_sessions(self, user_id: int, reason: str = None) -> bool:
        """
        Handle session revocation from auth service
        """
        try:
            with transaction_context() as session:
                user = User.query.get(user_id)
                if user:
                    user.last_login_at = None
                return True
        except Exception as e:
            logger.error(f"Error revoking user sessions: {str(e)}")
            return False

    def get_current_user(self) -> Optional[User]:
        """Get current authenticated user"""
        try:
            token = request.headers.get('Authorization', '').split(' ')[1]
            payload = self.validate_token(token)
            if not payload:
                return None
                
            return User.query.get(payload.get('user_id'))
            
        except Exception as e:
            logger.error(f"Error getting current user: {str(e)}")
            return None 
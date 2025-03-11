"""
Unit tests for the token service.
"""

import pytest
import jwt
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add pytest mark for test categories
pytestmark = [pytest.mark.unit, pytest.mark.auth, pytest.mark.service]


class TestTokenService:
    """Unit tests for the token service."""
    
    def test_create_access_token(self, app):
        """Test creating an access token."""
        with app.app_context():
            from src.services.token_service import create_access_token
            
            # Create token
            user_id = 1
            token = create_access_token(identity=user_id)
            
            # Verify token
            assert token is not None
            assert isinstance(token, str)
            
            # Decode and verify token
            secret_key = app.config['JWT_SECRET_KEY']
            algorithm = 'HS256'
            decoded = jwt.decode(token, secret_key, algorithms=[algorithm])
            
            # Check token claims
            assert decoded['sub'] == user_id
            assert decoded['type'] == 'access'
            assert 'iat' in decoded  # Issued at
            assert 'exp' in decoded  # Expiration time
            
            # Verify expiration
            now = int(time.time())
            expires_in = app.config['JWT_ACCESS_TOKEN_EXPIRES']
            assert decoded['exp'] <= now + expires_in
    
    def test_create_refresh_token(self, app):
        """Test creating a refresh token."""
        with app.app_context():
            from src.services.token_service import create_refresh_token
            
            # Create token
            user_id = 1
            token = create_refresh_token(identity=user_id)
            
            # Verify token
            assert token is not None
            assert isinstance(token, str)
            
            # Decode and verify token
            secret_key = app.config['JWT_SECRET_KEY']
            algorithm = 'HS256'
            decoded = jwt.decode(token, secret_key, algorithms=[algorithm])
            
            # Check token claims
            assert decoded['sub'] == user_id
            assert decoded['type'] == 'refresh'
            assert 'iat' in decoded  # Issued at
            assert 'exp' in decoded  # Expiration time
            
            # Verify expiration
            now = int(time.time())
            expires_in = app.config['JWT_REFRESH_TOKEN_EXPIRES']
            assert decoded['exp'] <= now + expires_in
    
    def test_create_service_token(self, app):
        """Test creating a service token."""
        with app.app_context():
            from src.services.token_service import create_service_token
            
            # Create token
            issuer = 'auth-service'
            audience = 'backend-service'
            token = create_service_token(issuer=issuer, audience=audience)
            
            # Verify token
            assert token is not None
            assert isinstance(token, str)
            
            # Decode and verify token
            secret_key = app.config['SERVICE_KEY']
            algorithm = 'HS256'
            decoded = jwt.decode(token, secret_key, algorithms=[algorithm], audience=audience)
            
            # Check token claims
            assert decoded['iss'] == issuer
            assert decoded['aud'] == audience
            assert decoded['type'] == 'service'
            assert 'iat' in decoded  # Issued at
            assert 'exp' in decoded  # Expiration time
    
    def test_decode_token_valid(self, app):
        """Test decoding a valid token."""
        with app.app_context():
            from src.services.token_service import decode_token, create_access_token
            
            # Create token
            user_id = 1
            token = create_access_token(identity=user_id)
            
            # Decode token
            decoded = decode_token(token)
            
            # Verify decoded token
            assert decoded is not None
            assert decoded['sub'] == user_id
            assert decoded['type'] == 'access'
    
    def test_decode_token_invalid(self, app):
        """Test decoding an invalid token."""
        with app.app_context():
            from src.services.token_service import decode_token
            from src.core.errors import TokenError
            
            # Create invalid token
            token = "invalid.token.string"
            
            # Attempt to decode token
            with pytest.raises(TokenError):
                decode_token(token)
    
    def test_decode_token_expired(self, app, monkeypatch):
        """Test decoding an expired token."""
        with app.app_context():
            from src.services.token_service import decode_token, create_access_token
            from src.core.errors import TokenError
            
            # Mock the JWT decode function to raise an ExpiredSignatureError
            def mock_decode(*args, **kwargs):
                raise jwt.ExpiredSignatureError("Token expired")
            
            # Create token
            user_id = 1
            token = create_access_token(identity=user_id)
            
            # Mock the jwt.decode function
            monkeypatch.setattr(jwt, 'decode', mock_decode)
            
            # Attempt to decode token
            with pytest.raises(TokenError) as excinfo:
                decode_token(token)
            
            # Verify the error message
            assert "Token has expired" in str(excinfo.value)
    
    def test_validate_token_valid(self, app):
        """Test validating a valid token."""
        with app.app_context():
            from src.services.token_service import validate_token, create_access_token
            
            # Create token
            user_id = 1
            token = create_access_token(identity=user_id)
            
            # Validate token
            is_valid, claims = validate_token(token)
            
            # Verify validation result
            assert is_valid is True
            assert claims is not None
            assert claims['sub'] == user_id
    
    def test_validate_token_invalid(self, app):
        """Test validating an invalid token."""
        with app.app_context():
            from src.services.token_service import validate_token
            
            # Create invalid token
            token = "invalid.token.string"
            
            # Validate token
            is_valid, claims = validate_token(token)
            
            # Verify validation result
            assert is_valid is False
            assert claims is None
    
    def test_validate_token_with_redis_blacklist(self, app):
        """Test validating a token against the Redis blacklist."""
        with app.app_context():
            from src.services.token_service import validate_token, create_access_token
            import fakeredis
            
            # Mock Redis client
            redis_client = fakeredis.FakeStrictRedis()
            
            # Create token
            user_id = 1
            token = create_access_token(identity=user_id)
            
            # Decode token to get jti
            secret_key = app.config['JWT_SECRET_KEY']
            algorithm = 'HS256'
            decoded = jwt.decode(token, secret_key, algorithms=[algorithm])
            jti = decoded.get('jti', '')
            
            # Test with token not in blacklist
            with patch('src.services.token_service.redis_client', redis_client):
                is_valid, claims = validate_token(token)
                assert is_valid is True
                assert claims is not None
            
            # Add token to blacklist
            redis_client.set(f"token:blacklist:{jti}", "1")
            
            # Test with token in blacklist
            with patch('src.services.token_service.redis_client', redis_client):
                is_valid, claims = validate_token(token)
                assert is_valid is False
                assert claims is None 
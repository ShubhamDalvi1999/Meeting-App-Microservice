"""
Unit tests for the authentication service.
"""

import pytest
import bcrypt
from unittest.mock import patch, MagicMock

# Add pytest mark for test categories
pytestmark = [pytest.mark.unit, pytest.mark.auth, pytest.mark.service]


class TestAuthService:
    """Unit tests for the auth service."""
    
    def test_hash_password(self, app):
        """Test hashing a password."""
        with app.app_context():
            from src.services.auth_service import hash_password
            
            # Hash password
            password = "TestPassword123!"
            hashed = hash_password(password)
            
            # Verify hash
            assert hashed is not None
            assert isinstance(hashed, str)
            assert hashed != password
            
            # Verify that bcrypt can verify the password
            assert bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def test_verify_password(self, app):
        """Test verifying a password."""
        with app.app_context():
            from src.services.auth_service import verify_password, hash_password
            
            # Hash password
            password = "TestPassword123!"
            hashed = hash_password(password)
            
            # Verify correct password
            result = verify_password(password, hashed)
            assert result is True
            
            # Verify incorrect password
            result = verify_password("WrongPassword123!", hashed)
            assert result is False
    
    def test_register_user_success(self, app, db):
        """Test successful user registration."""
        with app.app_context():
            from src.services.auth_service import register_user
            from src.models.user import User
            
            # Register user
            email = "new_user@example.com"
            password = "NewPassword123!"
            name = "New User"
            
            user = register_user(email=email, password=password, name=name)
            
            # Verify user was created
            assert user is not None
            assert user.email == email
            assert user.name == name
            assert user.password_hash is not None
            assert user.id is not None
            
            # Verify user exists in database
            db_user = User.query.filter_by(email=email).first()
            assert db_user is not None
            assert db_user.id == user.id
    
    def test_register_user_duplicate_email(self, app, db, test_user):
        """Test registration with a duplicate email."""
        with app.app_context():
            from src.services.auth_service import register_user
            from src.core.errors import UserExistsError
            
            # Attempt to register with existing email
            with pytest.raises(UserExistsError):
                register_user(
                    email=test_user['email'],
                    password="NewPassword123!",
                    name="Duplicate User"
                )
    
    def test_authenticate_user_success(self, app, db, test_user):
        """Test successful user authentication."""
        with app.app_context():
            from src.services.auth_service import authenticate_user
            
            # Authenticate user
            user = authenticate_user(email=test_user['email'], password=test_user['password'])
            
            # Verify authentication
            assert user is not None
            assert user.email == test_user['email']
            assert user.id == test_user['id']
    
    def test_authenticate_user_invalid_email(self, app, db):
        """Test authentication with an invalid email."""
        with app.app_context():
            from src.services.auth_service import authenticate_user
            from src.core.errors import AuthenticationError
            
            # Attempt to authenticate with non-existent email
            with pytest.raises(AuthenticationError):
                authenticate_user(email="nonexistent@example.com", password="password")
    
    def test_authenticate_user_invalid_password(self, app, db, test_user):
        """Test authentication with an invalid password."""
        with app.app_context():
            from src.services.auth_service import authenticate_user
            from src.core.errors import AuthenticationError
            
            # Attempt to authenticate with incorrect password
            with pytest.raises(AuthenticationError):
                authenticate_user(email=test_user['email'], password="WrongPassword123!")
    
    def test_get_user_by_id(self, app, db, test_user):
        """Test getting a user by ID."""
        with app.app_context():
            from src.services.auth_service import get_user_by_id
            
            # Get user by ID
            user = get_user_by_id(test_user['id'])
            
            # Verify user
            assert user is not None
            assert user.id == test_user['id']
            assert user.email == test_user['email']
    
    def test_get_user_by_id_nonexistent(self, app, db):
        """Test getting a nonexistent user by ID."""
        with app.app_context():
            from src.services.auth_service import get_user_by_id
            
            # Attempt to get nonexistent user
            user = get_user_by_id(999)
            
            # Verify result
            assert user is None
    
    def test_get_user_by_email(self, app, db, test_user):
        """Test getting a user by email."""
        with app.app_context():
            from src.services.auth_service import get_user_by_email
            
            # Get user by email
            user = get_user_by_email(test_user['email'])
            
            # Verify user
            assert user is not None
            assert user.id == test_user['id']
            assert user.email == test_user['email']
    
    def test_get_user_by_email_nonexistent(self, app, db):
        """Test getting a nonexistent user by email."""
        with app.app_context():
            from src.services.auth_service import get_user_by_email
            
            # Attempt to get nonexistent user
            user = get_user_by_email("nonexistent@example.com")
            
            # Verify result
            assert user is None
    
    def test_update_user_profile(self, app, db, test_user):
        """Test updating a user's profile."""
        with app.app_context():
            from src.services.auth_service import update_user_profile
            
            # Update profile
            new_name = "Updated Name"
            user = update_user_profile(
                user_id=test_user['id'],
                name=new_name,
                profile_data={'bio': 'Test bio'}
            )
            
            # Verify update
            assert user is not None
            assert user.id == test_user['id']
            assert user.name == new_name
            assert user.profile_data.get('bio') == 'Test bio'
    
    def test_update_user_profile_nonexistent(self, app, db):
        """Test updating a nonexistent user's profile."""
        with app.app_context():
            from src.services.auth_service import update_user_profile
            from src.core.errors import UserNotFoundError
            
            # Attempt to update nonexistent user
            with pytest.raises(UserNotFoundError):
                update_user_profile(
                    user_id=999,
                    name="Updated Name",
                    profile_data={'bio': 'Test bio'}
                )
    
    def test_change_password(self, app, db, test_user):
        """Test changing a user's password."""
        with app.app_context():
            from src.services.auth_service import change_password, authenticate_user
            from src.core.errors import AuthenticationError
            
            # Change password
            old_password = test_user['password']
            new_password = "NewPassword123!"
            
            user = change_password(
                user_id=test_user['id'],
                current_password=old_password,
                new_password=new_password
            )
            
            # Verify password change
            assert user is not None
            assert user.id == test_user['id']
            
            # Old password should no longer work
            with pytest.raises(AuthenticationError):
                authenticate_user(email=test_user['email'], password=old_password)
            
            # New password should work
            authenticated_user = authenticate_user(email=test_user['email'], password=new_password)
            assert authenticated_user is not None
            assert authenticated_user.id == test_user['id']
    
    def test_change_password_incorrect_current(self, app, db, test_user):
        """Test changing a password with incorrect current password."""
        with app.app_context():
            from src.services.auth_service import change_password
            from src.core.errors import AuthenticationError
            
            # Attempt to change password with incorrect current password
            with pytest.raises(AuthenticationError):
                change_password(
                    user_id=test_user['id'],
                    current_password="WrongPassword123!",
                    new_password="NewPassword123!"
                )
    
    def test_reset_password_flow(self, app, db, test_user):
        """Test the password reset flow."""
        with app.app_context():
            from src.services.auth_service import generate_password_reset_token, verify_reset_token, reset_password
            
            # Generate reset token
            token = generate_password_reset_token(test_user['email'])
            
            # Verify token is valid
            assert token is not None
            email = verify_reset_token(token)
            assert email == test_user['email']
            
            # Reset password
            new_password = "ResetPassword123!"
            user = reset_password(token, new_password)
            
            # Verify password reset
            assert user is not None
            assert user.id == test_user['id']
            
            # Verify new password
            from src.services.auth_service import authenticate_user
            auth_user = authenticate_user(email=test_user['email'], password=new_password)
            assert auth_user is not None
            assert auth_user.id == test_user['id']
    
    def test_verify_reset_token_invalid(self, app):
        """Test verifying an invalid reset token."""
        with app.app_context():
            from src.services.auth_service import verify_reset_token
            from src.core.errors import TokenError
            
            # Create invalid token
            token = "invalid-token"
            
            # Verify token
            with pytest.raises(TokenError):
                verify_reset_token(token) 
from datetime import datetime, timedelta
from sqlalchemy.sql import func
import bcrypt
from ..schemas.auth import AuthUserCreate, AuthUserUpdate, AuthUserResponse, SessionCreate, EmailVerificationCreate
from ..database import db

class AuthUser(db.Model):
    __tablename__ = 'auth_users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=True)
    is_google_user = db.Column(db.Boolean, default=False)
    first_login = db.Column(db.Boolean, default=True)
    is_email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    last_login = db.Column(db.DateTime)
    
    # Profile fields
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    profile_picture = db.Column(db.String(255))
    
    # OAuth fields
    google_id = db.Column(db.String(255), unique=True, nullable=True)
    google_refresh_token = db.Column(db.Text, nullable=True)

    # Account security fields
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    password_last_changed = db.Column(db.DateTime, default=func.now())
    require_password_change = db.Column(db.Boolean, default=False)
    last_failed_login = db.Column(db.DateTime, nullable=True)
    security_audit_log = db.Column(db.JSON, nullable=True)

    @classmethod
    def from_schema(cls, user_create: AuthUserCreate):
        """Create a new user from schema"""
        user = cls(
            email=user_create.email.lower(),
            first_name=user_create.first_name,
            last_name=user_create.last_name
        )
        user.set_password(user_create.password)
        return user

    def update_from_schema(self, user_update: AuthUserUpdate):
        """Update user from schema"""
        for field, value in user_update.model_dump(exclude_unset=True).items():
            setattr(self, field, value)

    def to_schema(self) -> AuthUserResponse:
        """Convert to response schema"""
        return AuthUserResponse.model_validate(self)

    def set_password(self, password: str):
        """Hash and set the user's password with history tracking"""
        if not password:
            raise ValueError("Password cannot be empty")
            
        # Check password history
        if self.password_hash:
            # Store old password in history
            history = PasswordHistory(
                user_id=self.id,
                password_hash=self.password_hash
            )
            db.session.add(history)
            
            # Check if password was used recently
            recent_passwords = PasswordHistory.query.filter_by(
                user_id=self.id
            ).order_by(PasswordHistory.created_at.desc()).limit(5).all()
            
            for old_pw in recent_passwords:
                if bcrypt.checkpw(password.encode('utf-8'), old_pw.password_hash.encode('utf-8')):
                    raise ValueError("Password was used recently. Please choose a different password.")

        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        self.password_last_changed = datetime.utcnow()
        self.require_password_change = False
        
        # Log password change
        self._log_security_event("password_changed")

    def check_password(self, password: str) -> bool:
        """Verify the user's password with account lockout"""
        if self.is_locked():
            return False
            
        if not self.password_hash:
            return False
            
        is_valid = bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        
        if not is_valid:
            self.failed_login_attempts += 1
            self.last_failed_login = datetime.utcnow()
            
            # Lock account after 5 failed attempts
            if self.failed_login_attempts >= 5:
                self.locked_until = datetime.utcnow() + timedelta(minutes=15)
                self._log_security_event("account_locked", {"reason": "too_many_failed_attempts"})
            
            db.session.commit()
            return False
            
        # Reset failed attempts on successful login
        self.failed_login_attempts = 0
        self.locked_until = None
        db.session.commit()
        return True

    def is_locked(self) -> bool:
        """Check if the account is locked"""
        if not self.locked_until:
            return False
        return datetime.utcnow() < self.locked_until

    def unlock(self):
        """Unlock the account"""
        self.locked_until = None
        self.failed_login_attempts = 0
        self._log_security_event("account_unlocked")
        db.session.commit()

    def force_password_change(self):
        """Force user to change password on next login"""
        self.require_password_change = True
        self._log_security_event("password_change_required")
        db.session.commit()

    def _log_security_event(self, event_type: str, details: dict = None):
        """Log security-related events"""
        if self.security_audit_log is None:
            self.security_audit_log = []
            
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }
        
        self.security_audit_log.append(event)
        if len(self.security_audit_log) > 100:  # Keep last 100 events
            self.security_audit_log = self.security_audit_log[-100:]

    def create_session(self, device_info=None, expires_at=None) -> 'UserSession':
        """Create a new session for the user"""
        session_data = SessionCreate(
            user_id=self.id,
            device_info=device_info,
            ip_address=device_info.get('ip_address') if device_info else None,
            expires_at=expires_at or datetime.utcnow() + timedelta(days=7)
        )
        session = UserSession.from_schema(session_data)
        db.session.add(session)
        return session

    def create_verification_token(self) -> 'EmailVerification':
        """Create a new email verification token"""
        import secrets
        token_data = EmailVerificationCreate(
            user_id=self.id,
            token=secrets.token_urlsafe(32),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        verification = EmailVerification.from_schema(token_data)
        db.session.add(verification)
        return verification

class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('auth_users.id', ondelete='CASCADE'), nullable=False)
    token = db.Column(db.Text, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=func.now())
    used = db.Column(db.Boolean, default=False)

    user = db.relationship('AuthUser', backref=db.backref('reset_tokens', lazy=True))

    @classmethod
    def from_schema(cls, token_data):
        return cls(
            user_id=token_data.user_id,
            token=token_data.token,
            expires_at=token_data.expires_at
        )

class UserSession(db.Model):
    __tablename__ = 'user_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('auth_users.id', ondelete='CASCADE'), nullable=False)
    token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text, nullable=True)
    device_info = db.Column(db.JSON, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=func.now())
    expires_at = db.Column(db.DateTime, nullable=False)
    refresh_token_expires_at = db.Column(db.DateTime, nullable=True)
    revoked = db.Column(db.Boolean, default=False)
    revoked_at = db.Column(db.DateTime, nullable=True)
    revocation_reason = db.Column(db.String(100), nullable=True)
    last_used_at = db.Column(db.DateTime, nullable=True)
    device_name = db.Column(db.String(100), nullable=True)
    device_type = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)

    user = db.relationship('AuthUser', backref=db.backref('sessions', lazy=True))

    @classmethod
    def from_schema(cls, session_data: SessionCreate):
        import secrets
        return cls(
            user_id=session_data.user_id,
            token=secrets.token_urlsafe(32),
            refresh_token=secrets.token_urlsafe(32) if session_data.include_refresh_token else None,
            device_info=session_data.device_info,
            ip_address=session_data.ip_address,
            expires_at=session_data.expires_at,
            refresh_token_expires_at=session_data.refresh_token_expires_at,
            device_name=session_data.device_info.get('name') if session_data.device_info else None,
            device_type=session_data.device_info.get('type') if session_data.device_info else None,
            user_agent=session_data.device_info.get('user_agent') if session_data.device_info else None
        )

    def revoke(self, reason: str = None):
        """Revoke the session"""
        self.revoked = True
        self.revoked_at = datetime.utcnow()
        self.revocation_reason = reason
        db.session.commit()

    def refresh(self) -> 'UserSession':
        """Create a new session using the refresh token"""
        if self.revoked or not self.refresh_token or datetime.utcnow() > self.refresh_token_expires_at:
            raise ValueError("Invalid or expired refresh token")
        
        import secrets
        new_session = UserSession(
            user_id=self.user_id,
            token=secrets.token_urlsafe(32),
            refresh_token=secrets.token_urlsafe(32),
            device_info=self.device_info,
            ip_address=self.ip_address,
            expires_at=datetime.utcnow() + timedelta(days=1),
            refresh_token_expires_at=datetime.utcnow() + timedelta(days=30),
            device_name=self.device_name,
            device_type=self.device_type,
            user_agent=self.user_agent
        )
        
        self.revoke("Refreshed")
        db.session.add(new_session)
        db.session.commit()
        return new_session

    def update_last_used(self):
        """Update the last used timestamp"""
        self.last_used_at = datetime.utcnow()
        db.session.commit()

class EmailVerification(db.Model):
    __tablename__ = 'email_verifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('auth_users.id', ondelete='CASCADE'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=func.now())
    is_used = db.Column(db.Boolean, default=False)

    user = db.relationship('AuthUser', backref=db.backref('email_verifications', lazy=True))

    @classmethod
    def from_schema(cls, verification_data: EmailVerificationCreate):
        return cls(
            user_id=verification_data.user_id,
            token=verification_data.token,
            expires_at=verification_data.expires_at
        )

class PasswordHistory(db.Model):
    __tablename__ = 'password_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('auth_users.id', ondelete='CASCADE'), nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=func.now())

    user = db.relationship('AuthUser', backref=db.backref('password_history', lazy=True)) 
# Security Documentation

## Authentication System

### User Model Security Features

#### Core Fields
- `id`: Primary key, auto-incrementing integer
- `email`: Unique, indexed, case-insensitive (max 120 chars)
- `name`: Unique, indexed, case-insensitive (max 100 chars)
- `password_hash`: Securely hashed using bcrypt (max 128 chars)

#### Security Fields
- `is_active`: Boolean flag for account status
- `is_email_verified`: Email verification status
- `email_verification_token`: Unique token for email verification
- `email_verification_sent_at`: Timestamp of verification email
- `last_password_change`: Timestamp of last password update

#### Account Protection
- `failed_login_attempts`: Counter for failed attempts
- `locked_until`: Timestamp until account is unlocked
- `login_count`: Total successful login counter
- `last_login_at`: Timestamp of last login
- `last_login_ip`: IP address of last login (IPv6 compatible)

### Registration Security (/api/auth/register)

#### Input Validation
1. Email Requirements:
   - Valid email format (RFC compliant)
   - Maximum length: 120 characters
   - Case-insensitive uniqueness check
   - Automatic trimming and lowercase conversion

2. Password Requirements:
   - Minimum length: 8 characters
   - Maximum length: 72 characters (bcrypt limit)
   - Must contain:
     - At least one uppercase letter
     - At least one lowercase letter
     - At least one number
     - At least one special character (!@#$%^&*(),.?":{}|<>)

3. Name Requirements:
   - Length: 3-100 characters
   - Allowed characters: letters, numbers, spaces, dots, hyphens
   - Case-insensitive uniqueness check
   - Automatic trimming

#### Security Measures
1. Rate Limiting:
   - IP-based request limiting
   - Configurable thresholds
   - Automatic blocking after threshold breach

2. Data Protection:
   - Input sanitization
   - SQL injection prevention
   - XSS protection
   - CSRF protection

3. Response Security:
   - No sensitive data in responses
   - Appropriate HTTP status codes
   - Detailed error messages without exposing internals

### Login Security (/api/auth/login)

#### Authentication Process
1. Rate Limiting:
   - Account-based attempt limiting (5 attempts)
   - IP-based request limiting
   - 15-minute lockout after failed attempts

2. Credential Verification:
   - Case-insensitive email lookup
   - Secure password comparison
   - Prevention of timing attacks

3. Session Management:
   - JWT token generation
   - Configurable token expiry
   - Token rotation on password change

#### Security Features
1. Account Protection:
   - Failed attempt tracking
   - Automatic account locking
   - IP address logging
   - Login time tracking

2. Response Security:
   - Remaining attempt count in responses
   - Lock duration information
   - Generic error messages for invalid credentials

3. Token Security:
   - JWT with multiple claims (iat, exp, type)
   - Secure token generation
   - Token verification endpoint

### Password Reset Security

1. Token Generation:
   - Secure random token generation
   - Limited token validity (24 hours)
   - One-time use enforcement

2. Process Security:
   - Rate limiting for reset requests
   - Email verification required
   - Previous password history check

### Email Verification

1. Verification Process:
   - Secure token generation
   - 24-hour token expiry
   - One-time use tokens

2. Security Measures:
   - Rate limiting for verification emails
   - Prevention of email enumeration
   - Secure token storage

## Best Practices Implementation

### Database Security
1. Data Protection:
   - Indexed sensitive fields
   - Proper column length constraints
   - Secure default values
   - Audit timestamps

2. Query Security:
   - Prepared statements
   - Input validation
   - Case-insensitive comparisons
   - Transaction management

### API Security
1. Request Protection:
   - Input validation
   - Rate limiting
   - IP blocking
   - Request size limiting

2. Response Security:
   - No sensitive data exposure
   - Proper status codes
   - Detailed error messages
   - Security headers

### Error Handling
1. User Errors:
   - Descriptive messages
   - Validation requirements
   - Remaining attempts info
   - Lock duration info

2. System Errors:
   - Generic error messages
   - No stack traces in production
   - Proper logging
   - Error tracking

## Security Recommendations

### For Developers
1. Always use prepared statements
2. Validate all user input
3. Implement rate limiting
4. Use secure password hashing
5. Implement proper logging

### For Deployment
1. Use HTTPS only
2. Set secure headers
3. Configure rate limiting
4. Enable monitoring
5. Regular security updates

### For Users
1. Use strong passwords
2. Enable email verification
3. Monitor login activity
4. Report suspicious activity
5. Regular password changes 
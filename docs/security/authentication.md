# Authentication Documentation

## API Endpoints

### 1. Registration
```http
POST /api/auth/register
Content-Type: application/json

{
    "email": "user@example.com",
    "name": "John Doe",
    "password": "SecureP@ss123"
}
```

#### Success Response (201 Created)
```json
{
    "message": "User registered successfully",
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "name": "John Doe",
        "is_active": true,
        "is_email_verified": false,
        "created_at": "2024-01-20T10:00:00Z",
        "updated_at": "2024-01-20T10:00:00Z"
    }
}
```

#### Error Responses
```json
// 400 Bad Request - Invalid Email
{
    "error": "Invalid email format or length",
    "requirements": "Valid email format and maximum 120 characters"
}

// 400 Bad Request - Invalid Password
{
    "error": "Password does not meet requirements",
    "requirements": "At least 8 characters, 1 uppercase, 1 lowercase, 1 number, 1 special character"
}

// 400 Bad Request - Invalid Name
{
    "error": "Invalid name format or length",
    "requirements": "Between 3-100 characters, letters, numbers, spaces, dots, and hyphens only"
}

// 400 Bad Request - Duplicate Email
{
    "error": "Email already registered"
}

// 429 Too Many Requests
{
    "error": "Too many requests",
    "code": "ip_blocked"
}
```

### 2. Login
```http
POST /api/auth/login
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "SecureP@ss123"
}
```

#### Success Response (200 OK)
```json
{
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "name": "John Doe",
        "is_active": true,
        "is_email_verified": true,
        "created_at": "2024-01-20T10:00:00Z",
        "updated_at": "2024-01-20T10:00:00Z",
        "last_login_at": "2024-01-20T15:30:00Z"
    }
}
```

#### Error Responses
```json
// 401 Unauthorized - Invalid Credentials
{
    "error": "Invalid credentials",
    "remaining_attempts": 4
}

// 429 Too Many Requests - Account Locked
{
    "error": "Account temporarily locked",
    "code": "account_locked",
    "retry_after": "15 minutes"
}

// 429 Too Many Requests - IP Blocked
{
    "error": "Too many requests",
    "code": "ip_blocked"
}
```

### 3. Token Verification
```http
POST /api/auth/verify-token
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

#### Success Response (200 OK)
```json
{
    "valid": true,
    "user": {
        "id": 1,
        "email": "user@example.com",
        "name": "John Doe",
        "is_active": true,
        "is_email_verified": true,
        "created_at": "2024-01-20T10:00:00Z",
        "updated_at": "2024-01-20T10:00:00Z"
    }
}
```

#### Error Responses
```json
// 401 Unauthorized - Expired Token
{
    "error": "Token has expired",
    "code": "token_expired"
}

// 401 Unauthorized - Invalid Token
{
    "error": "Invalid token",
    "code": "token_invalid"
}
```

## Implementation Details

### JWT Token Structure
```json
{
    "user_id": 1,
    "email": "user@example.com",
    "exp": 1674307200,  // Expiration time
    "iat": 1674220800,  // Issued at time
    "type": "access"    // Token type
}
```

### Security Features
1. **Rate Limiting**:
   - Registration: 5 requests per IP per hour
   - Login: 5 attempts per account per 15 minutes
   - Token verification: 60 requests per minute

2. **Password Requirements**:
   ```python
   def validate_password(password):
       if not password or len(password) > 72:  # bcrypt limit
           return False
       if len(password) < 8:
           return False
       if not re.search(r'[A-Z]', password):
           return False
       if not re.search(r'[a-z]', password):
           return False
       if not re.search(r'[0-9]', password):
           return False
       if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
           return False
       return True
   ```

3. **Email Validation**:
   ```python
   def validate_email(email):
       if not email or len(email) > 120:
           return False
       pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
       return re.match(pattern, email) is not None
   ```

## Usage Examples

### Frontend Login Implementation
```typescript
async function login(email: string, password: string) {
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            if (response.status === 429) {
                // Handle account lock or rate limit
                const retryAfter = data.retry_after;
                throw new Error(`Account locked. Try again in ${retryAfter}`);
            }
            if (response.status === 401) {
                // Handle invalid credentials
                const remainingAttempts = data.remaining_attempts;
                throw new Error(`Invalid credentials. ${remainingAttempts} attempts remaining`);
            }
            throw new Error(data.error);
        }

        // Store token and user data
        localStorage.setItem('token', data.token);
        return data.user;
    } catch (error) {
        console.error('Login failed:', error);
        throw error;
    }
}
```

### Token Verification Example
```typescript
async function verifyToken(token: string) {
    try {
        const response = await fetch('/api/auth/verify-token', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        const data = await response.json();

        if (!response.ok) {
            if (data.code === 'token_expired') {
                // Handle expired token
                localStorage.removeItem('token');
                window.location.href = '/login';
            }
            throw new Error(data.error);
        }

        return data.user;
    } catch (error) {
        console.error('Token verification failed:', error);
        throw error;
    }
} 
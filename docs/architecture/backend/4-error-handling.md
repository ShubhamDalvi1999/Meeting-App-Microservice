# 4. Error Handling

## Overview
This document covers error handling strategies in our Flask backend application. Proper error handling is crucial for maintaining application stability and providing meaningful feedback to users.

## Custom Exceptions

### 1. Base Exceptions
```python
# src/exceptions/base.py
from typing import Dict, Any, Optional

class AppError(Exception):
    """Base exception for application errors."""
    def __init__(
        self,
        message: str,
        code: str = 'INTERNAL_ERROR',
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format."""
        return {
            'error': {
                'code': self.code,
                'message': self.message,
                'details': self.details
            }
        }

class ValidationError(AppError):
    """Exception for validation errors."""
    def __init__(
        self,
        message: str = 'Validation error',
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code='VALIDATION_ERROR',
            status_code=400,
            details=details
        )

class NotFoundError(AppError):
    """Exception for resource not found errors."""
    def __init__(
        self,
        resource: str,
        resource_id: Any
    ):
        super().__init__(
            message=f'{resource} with id {resource_id} not found',
            code='NOT_FOUND',
            status_code=404,
            details={
                'resource': resource,
                'resource_id': resource_id
            }
        )

class AuthenticationError(AppError):
    """Exception for authentication errors."""
    def __init__(
        self,
        message: str = 'Authentication failed'
    ):
        super().__init__(
            message=message,
            code='AUTHENTICATION_ERROR',
            status_code=401
        )

class AuthorizationError(AppError):
    """Exception for authorization errors."""
    def __init__(
        self,
        message: str = 'Insufficient permissions',
        required_permissions: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            code='AUTHORIZATION_ERROR',
            status_code=403,
            details={'required_permissions': required_permissions}
        )
```

### 2. Domain-Specific Exceptions
```python
# src/exceptions/meeting.py
from src.exceptions.base import AppError
from datetime import datetime

class MeetingConflictError(AppError):
    """Exception for meeting time conflicts."""
    def __init__(
        self,
        start_time: datetime,
        end_time: datetime,
        conflicting_meetings: List[Dict[str, Any]]
    ):
        super().__init__(
            message='Meeting time conflicts with existing meetings',
            code='MEETING_CONFLICT',
            status_code=409,
            details={
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'conflicting_meetings': conflicting_meetings
            }
        )

class MeetingCapacityError(AppError):
    """Exception for meeting capacity issues."""
    def __init__(
        self,
        meeting_id: int,
        current_capacity: int,
        max_capacity: int
    ):
        super().__init__(
            message='Meeting has reached maximum capacity',
            code='MEETING_CAPACITY_ERROR',
            status_code=400,
            details={
                'meeting_id': meeting_id,
                'current_capacity': current_capacity,
                'max_capacity': max_capacity
            }
        )
```

## Error Handlers

### 1. Global Error Handler
```python
# src/error_handlers.py
from flask import jsonify
from src.exceptions import AppError
from sqlalchemy.exc import SQLAlchemyError
from jwt.exceptions import PyJWTError

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        """Handle custom application errors."""
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(error):
        """Handle database errors."""
        app.logger.error(f'Database error: {str(error)}')
        return jsonify({
            'error': {
                'code': 'DATABASE_ERROR',
                'message': 'A database error occurred'
            }
        }), 500

    @app.errorhandler(PyJWTError)
    def handle_jwt_error(error):
        """Handle JWT errors."""
        return jsonify({
            'error': {
                'code': 'INVALID_TOKEN',
                'message': 'Invalid or expired token'
            }
        }), 401

    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 errors."""
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Resource not found'
            }
        }), 404

    @app.errorhandler(500)
    def handle_server_error(error):
        """Handle internal server errors."""
        app.logger.error(f'Server error: {str(error)}')
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An internal server error occurred'
            }
        }), 500
```

### 2. Route-Specific Error Handlers
```python
# src/routes/meetings.py
from flask import Blueprint, request
from src.services import meeting_service
from src.exceptions import (
    ValidationError,
    NotFoundError,
    MeetingConflictError
)

meetings_bp = Blueprint('meetings', __name__)

@meetings_bp.errorhandler(ValidationError)
def handle_validation_error(error):
    """Handle validation errors in meetings routes."""
    response = {
        'error': {
            'code': 'MEETING_VALIDATION_ERROR',
            'message': str(error),
            'fields': error.details
        }
    }
    return response, 400

@meetings_bp.errorhandler(MeetingConflictError)
def handle_meeting_conflict(error):
    """Handle meeting conflict errors."""
    return error.to_dict(), error.status_code

@meetings_bp.route('/<int:meeting_id>', methods=['GET'])
def get_meeting(meeting_id):
    try:
        meeting = meeting_service.get_meeting(meeting_id)
        return jsonify(meeting.to_dict())
    except NotFoundError as e:
        return e.to_dict(), e.status_code
```

## Error Logging

### 1. Logger Configuration
```python
# src/logging_config.py
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging(app):
    """Configure application logging."""
    if not os.path.exists('logs'):
        os.mkdir('logs')

    # File handler
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=1024 * 1024,  # 1MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(levelname)s: %(message)s'
    ))
    console_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(console_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Application startup')
```

### 2. Error Logging Service
```python
# src/services/error_logging_service.py
from typing import Dict, Any, Optional
import logging
from datetime import datetime
from src.models import ErrorLog
from src import db

class ErrorLoggingService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def log_error(
        self,
        error: Exception,
        user_id: Optional[int] = None,
        request_data: Optional[Dict[str, Any]] = None
    ):
        """Log error to database and logging system."""
        try:
            # Create error log entry
            error_log = ErrorLog(
                error_type=type(error).__name__,
                error_message=str(error),
                stack_trace=getattr(error, '__traceback__', None),
                user_id=user_id,
                request_data=request_data,
                timestamp=datetime.utcnow()
            )
            db.session.add(error_log)
            db.session.commit()

            # Log to file system
            self.logger.error(
                f'Error occurred: {type(error).__name__}',
                exc_info=error,
                extra={
                    'user_id': user_id,
                    'request_data': request_data
                }
            )
        except Exception as e:
            # Fallback logging if database logging fails
            self.logger.critical(
                f'Failed to log error: {str(e)}',
                exc_info=True
            )

    def get_recent_errors(
        self,
        limit: int = 100
    ) -> List[ErrorLog]:
        """Get recent error logs."""
        return ErrorLog.query.order_by(
            ErrorLog.timestamp.desc()
        ).limit(limit).all()

    def get_error_stats(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get error statistics for a date range."""
        stats = db.session.query(
            ErrorLog.error_type,
            db.func.count(ErrorLog.id).label('count')
        ).filter(
            ErrorLog.timestamp.between(start_date, end_date)
        ).group_by(
            ErrorLog.error_type
        ).all()

        return {
            'total_errors': sum(s.count for s in stats),
            'error_types': {
                s.error_type: s.count for s in stats
            }
        }

error_logging_service = ErrorLoggingService()
```

## Error Recovery

### 1. Retry Mechanism
```python
# src/utils/retry.py
from functools import wraps
import time
from typing import Type, Tuple, Optional, Callable

def retry(
    exceptions: Tuple[Type[Exception], ...],
    tries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    logger: Optional[Callable] = None
):
    """Retry decorator with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 0:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    mtries -= 1
                    if mtries == 0:
                        raise

                    if logger:
                        logger(
                            f'Retrying {func.__name__} in {mdelay} seconds... '
                            f'Error: {str(e)}'
                        )

                    time.sleep(mdelay)
                    mdelay *= backoff
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Usage example
@retry(
    exceptions=(ConnectionError, TimeoutError),
    tries=3,
    delay=1,
    logger=app.logger.warning
)
def fetch_external_data():
    # Implementation
    pass
```

### 2. Circuit Breaker
```python
# src/utils/circuit_breaker.py
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any
import threading

class CircuitState(Enum):
    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half_open'

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: int = 60,
        half_open_timeout: int = 30
    ):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_timeout = half_open_timeout
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.last_failure_time = None
        self.lock = threading.Lock()

    def __call__(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            with self.lock:
                if self.state == CircuitState.OPEN:
                    if self._should_attempt_reset():
                        self.state = CircuitState.HALF_OPEN
                    else:
                        raise CircuitBreakerError(
                            'Circuit breaker is OPEN'
                        )

            try:
                result = func(*args, **kwargs)
                with self.lock:
                    if self.state == CircuitState.HALF_OPEN:
                        self._reset()
                return result
            except Exception as e:
                with self.lock:
                    self._handle_failure()
                raise e

        return wrapper

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if not self.last_failure_time:
            return True
        
        elapsed = datetime.now() - self.last_failure_time
        return elapsed.total_seconds() >= self.reset_timeout

    def _handle_failure(self):
        """Handle a failure and potentially open the circuit."""
        self.failures += 1
        self.last_failure_time = datetime.now()
        
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def _reset(self):
        """Reset the circuit breaker to its initial state."""
        self.failures = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

# Usage example
@circuit_breaker
def call_external_service():
    # Implementation
    pass
```

## Best Practices

### 1. Error Prevention
- Validate input data thoroughly
- Use type hints and static typing
- Implement proper logging
- Use defensive programming
- Handle edge cases explicitly

### 2. Error Recovery
- Implement retry mechanisms
- Use circuit breakers
- Implement fallback mechanisms
- Handle partial failures
- Implement proper cleanup

### 3. Error Reporting
- Log errors with context
- Use structured logging
- Implement error monitoring
- Set up alerts for critical errors
- Track error patterns

## Common Pitfalls

### 1. Overly Broad Exception Handling
```python
# Bad: Catching all exceptions
try:
    do_something()
except Exception:  # Too broad
    pass  # Silent failure

# Good: Specific exception handling
try:
    do_something()
except ValueError as e:
    logger.error(f'Invalid value: {e}')
    raise ValidationError(str(e))
except ConnectionError as e:
    logger.error(f'Connection failed: {e}')
    raise ServiceUnavailableError(str(e))
```

### 2. Insufficient Error Context
```python
# Bad: Poor error context
def process_data(data):
    if not validate(data):
        raise ValidationError('Invalid data')

# Good: Detailed error context
def process_data(data):
    validation_errors = validate(data)
    if validation_errors:
        raise ValidationError(
            'Data validation failed',
            details=validation_errors
        )
```

## Next Steps
After mastering error handling, proceed to:
1. Testing (5_testing.md) 
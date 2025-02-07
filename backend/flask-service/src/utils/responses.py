from flask import jsonify
from typing import Any, Dict, Optional, Tuple, Union

def api_response(
    data: Optional[Dict[str, Any]] = None,
    message: Optional[str] = None,
    error: Optional[str] = None,
    code: Optional[str] = None,
    status_code: int = 200
) -> Tuple[Dict[str, Any], int]:
    """
    Create a standardized API response.
    
    Args:
        data: Optional dictionary of response data
        message: Optional success message
        error: Optional error message
        code: Optional error code
        status_code: HTTP status code (default: 200)
    
    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {}
    
    if data is not None:
        response.update(data)
    
    if message is not None:
        response['message'] = message
        
    if error is not None:
        response['error'] = error
        
    if code is not None:
        response['code'] = code
        
    return jsonify(response), status_code

def error_response(
    error: str,
    code: str,
    status_code: int = 400
) -> Tuple[Dict[str, Any], int]:
    """
    Create a standardized error response.
    
    Args:
        error: Error message
        code: Error code
        status_code: HTTP status code (default: 400)
    
    Returns:
        Tuple of (response_dict, status_code)
    """
    return api_response(error=error, code=code, status_code=status_code)

def success_response(
    data: Optional[Dict[str, Any]] = None,
    message: Optional[str] = None,
    status_code: int = 200
) -> Tuple[Dict[str, Any], int]:
    """
    Create a standardized success response.
    
    Args:
        data: Optional dictionary of response data
        message: Optional success message
        status_code: HTTP status code (default: 200)
    
    Returns:
        Tuple of (response_dict, status_code)
    """
    return api_response(data=data, message=message, status_code=status_code) 
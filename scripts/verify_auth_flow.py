#!/usr/bin/env python
"""
Authentication Flow Verification Script.
Tests JWT token creation, verification, service integration, and error handling.
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
import time

# Default URLs (can be overridden with environment variables)
BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:5000/api")
AUTH_URL = os.environ.get("AUTH_URL", "http://localhost:5001/api/auth")

# Test credentials (should be updated with valid credentials)
TEST_EMAIL = os.environ.get("TEST_EMAIL", "admin@example.com")
TEST_PASSWORD = os.environ.get("TEST_PASSWORD", "admin123")

def log_response(response, operation):
    """Log API response details."""
    print(f"\n--- {operation} Response ---")
    print(f"Status: {response.status_code}")
    
    # Check for request ID in headers
    request_id = response.headers.get('X-Request-ID', 'Not present')
    correlation_id = response.headers.get('X-Correlation-ID', 'Not present')
    print(f"Request ID: {request_id}")
    print(f"Correlation ID: {correlation_id}")
    
    try:
        print(f"Body: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Body: {response.text[:200]}...")

def verify_auth_flow():
    """Test the JWT authentication flow and service integration."""
    print("\n=== Starting Authentication Flow Verification ===")
    
    # 1. Get auth token
    print("\nStep 1: Authenticating...")
    auth_response = requests.post(f"{AUTH_URL}/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if auth_response.status_code != 200:
        log_response(auth_response, "Authentication")
        print("❌ Authentication failed")
        return False
    
    token = auth_response.json().get("access_token")
    if not token:
        print("❌ No access token in response")
        return False
        
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Authentication successful")
    
    # 2. Verify token with auth service
    print("\nStep 2: Verifying token with auth service...")
    verify_response = requests.post(f"{AUTH_URL}/validate-token", 
                                  json={"token": token},
                                  headers={"X-Service-Key": os.environ.get("SERVICE_KEY", "test-service-key")})
    
    if verify_response.status_code != 200:
        log_response(verify_response, "Token Verification")
        print("❌ Token verification failed")
        return False
    
    print("✅ Token verification successful")
    
    # 3. Test protected endpoint
    print("\nStep 3: Accessing protected endpoint...")
    protected_response = requests.get(f"{BASE_URL}/meetings", headers=headers)
    
    if protected_response.status_code != 200:
        log_response(protected_response, "Protected Endpoint")
        print("❌ Protected endpoint access failed")
        return False
    
    print("✅ Protected endpoint access successful")
    
    # 4. Test expired/invalid token
    print("\nStep 4: Testing invalid token handling...")
    invalid_token = token + "invalid"
    invalid_headers = {"Authorization": f"Bearer {invalid_token}"}
    
    invalid_response = requests.get(f"{BASE_URL}/meetings", headers=invalid_headers)
    
    if invalid_response.status_code != 401:
        log_response(invalid_response, "Invalid Token")
        print("❌ Invalid token test failed - expected 401 status")
        return False
    
    # Check for proper error structure
    try:
        error_data = invalid_response.json()
        if "error" not in error_data or "message" not in error_data:
            print("❌ Error response missing required fields")
            return False
    except:
        print("❌ Error response not in JSON format")
        return False
    
    print("✅ Invalid token handling successful")
    
    # 5. Test service integration
    print("\nStep 5: Testing service integration...")
    
    # Test with missing service key
    service_response = requests.post(f"{AUTH_URL}/validate-token", 
                                   json={"token": token})
    
    if service_response.status_code != 403:
        log_response(service_response, "Missing Service Key")
        print("❌ Service key test failed - expected 403 status")
        return False
    
    print("✅ Service integration test successful")
    
    # 6. Test request ID propagation
    print("\nStep 6: Testing request ID propagation...")
    custom_request_id = f"test-{int(time.time())}"
    custom_headers = headers.copy()
    custom_headers["X-Request-ID"] = custom_request_id
    
    req_id_response = requests.get(f"{BASE_URL}/meetings", headers=custom_headers)
    
    if req_id_response.status_code != 200:
        log_response(req_id_response, "Request ID Test")
        print("❌ Request ID test failed")
        return False
    
    response_req_id = req_id_response.headers.get("X-Request-ID")
    if response_req_id != custom_request_id:
        print(f"❌ Request ID not propagated correctly. Expected: {custom_request_id}, Got: {response_req_id}")
        return False
    
    print("✅ Request ID propagation successful")
    
    # 7. Test correlation ID propagation
    print("\nStep 7: Testing correlation ID propagation...")
    custom_correlation_id = f"corr-{int(time.time())}"
    custom_headers = headers.copy()
    custom_headers["X-Correlation-ID"] = custom_correlation_id
    
    corr_id_response = requests.get(f"{BASE_URL}/meetings", headers=custom_headers)
    
    if corr_id_response.status_code != 200:
        log_response(corr_id_response, "Correlation ID Test")
        print("❌ Correlation ID test failed")
        return False
    
    response_corr_id = corr_id_response.headers.get("X-Correlation-ID")
    if response_corr_id != custom_correlation_id:
        print(f"❌ Correlation ID not propagated correctly. Expected: {custom_correlation_id}, Got: {response_corr_id}")
        return False
    
    print("✅ Correlation ID propagation successful")
    
    # 8. Test service discovery
    print("\nStep 8: Testing service discovery...")
    try:
        discovery_response = requests.get(f"{BASE_URL}/services")
        
        if discovery_response.status_code != 200:
            log_response(discovery_response, "Service Discovery")
            print("⚠️ Service discovery endpoint not available (this may be expected)")
        else:
            services = discovery_response.json()
            if not services or not isinstance(services, dict):
                print("⚠️ Service discovery returned unexpected format")
            else:
                print(f"✅ Service discovery returned {len(services)} services")
    except Exception as e:
        print(f"⚠️ Service discovery test failed: {str(e)}")
    
    print("\n=== Authentication Flow verification completed successfully! ===")
    return True

if __name__ == "__main__":
    try:
        if verify_auth_flow():
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during verification: {str(e)}")
        sys.exit(1) 
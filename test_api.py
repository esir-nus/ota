#!/usr/bin/env python3
import requests
import json

def test_status_endpoint():
    """Test the status endpoint."""
    print("\n== Testing Status Endpoint ==")
    url = "http://localhost:5000/api/v1/status"
    headers = {"X-API-Key": "admin-key-example"}
    
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200

def test_check_endpoint():
    """Test the check endpoint."""
    print("\n== Testing Check Endpoint ==")
    url = "http://localhost:5000/api/v1/check"
    headers = {"X-API-Key": "admin-key-example"}
    
    response = requests.post(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200

def test_apply_endpoint():
    """Test the apply endpoint."""
    print("\n== Testing Apply Endpoint ==")
    url = "http://localhost:5000/api/v1/apply"
    headers = {"X-API-Key": "admin-key-example"}
    
    response = requests.post(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200

def main():
    """Run all tests."""
    print("OTA API Testing")
    print("===============")
    
    status_ok = test_status_endpoint()
    check_ok = test_check_endpoint()
    apply_ok = test_apply_endpoint()
    
    print("\n== Test Results ==")
    print(f"Status Endpoint: {'OK' if status_ok else 'FAILED'}")
    print(f"Check Endpoint: {'OK' if check_ok else 'FAILED'}")
    print(f"Apply Endpoint: {'OK' if apply_ok else 'FAILED'}")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Test script for the Rock-Paper-Scissors FastAPI server.
Tests all endpoints without requiring hardware.
"""

import sys
from fastapi.testclient import TestClient

def test_api_structure():
    """Test that the API can be imported and all endpoints exist."""
    print("Testing API structure...")
    print("=" * 60)
    
    try:
        from api import app
        client = TestClient(app)
        
        print("✓ API imported successfully")
        print("✓ TestClient created")
        
        # Test root endpoint
        print("\n1. Testing root endpoint (GET /)...")
        response = client.get("/")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "name" in data, "Root endpoint missing 'name'"
        assert "endpoints" in data, "Root endpoint missing 'endpoints'"
        print(f"   ✓ Root endpoint OK: {data['name']}")
        
        # Test health endpoint
        print("\n2. Testing health endpoint (GET /health)...")
        response = client.get("/health")
        # May return 503 if robot not connected, that's OK
        assert response.status_code in [200, 503], f"Unexpected status code: {response.status_code}"
        data = response.json()
        assert "status" in data, "Health endpoint missing 'status'"
        print(f"   ✓ Health endpoint OK: status={data['status']}")
        
        # Test status endpoint
        print("\n3. Testing status endpoint (GET /status)...")
        response = client.get("/status")
        # May return 503 if robot not initialized, that's OK
        assert response.status_code in [200, 503], f"Unexpected status code: {response.status_code}"
        print(f"   ✓ Status endpoint OK: {response.status_code}")
        
        # Test OpenAPI docs
        print("\n4. Testing OpenAPI docs (GET /openapi.json)...")
        response = client.get("/openapi.json")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "openapi" in data, "OpenAPI schema missing 'openapi'"
        assert "paths" in data, "OpenAPI schema missing 'paths'"
        
        # Check all expected endpoints exist
        paths = data["paths"]
        expected_endpoints = [
            "/",
            "/health",
            "/status",
            "/connect",
            "/disconnect",
            "/rock",
            "/paper",
            "/scissors",
            "/random",
            "/shake",
            "/rest"
        ]
        
        for endpoint in expected_endpoints:
            assert endpoint in paths, f"Missing endpoint: {endpoint}"
            print(f"   ✓ Endpoint exists: {endpoint}")
        
        print("\n" + "=" * 60)
        print("✓ All API structure tests passed!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ API structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_endpoint_schemas():
    """Test that all gesture endpoints have correct request/response schemas."""
    print("\n\nTesting endpoint schemas...")
    print("=" * 60)
    
    try:
        from api import app
        client = TestClient(app)
        
        response = client.get("/openapi.json")
        schema = response.json()
        
        # Check rock endpoint schema
        print("\n1. Checking /rock endpoint schema...")
        rock_schema = schema["paths"]["/rock"]["post"]
        assert "responses" in rock_schema, "/rock missing responses"
        assert "200" in rock_schema["responses"], "/rock missing 200 response"
        print("   ✓ /rock schema OK")
        
        # Check paper endpoint schema
        print("\n2. Checking /paper endpoint schema...")
        paper_schema = schema["paths"]["/paper"]["post"]
        assert "responses" in paper_schema, "/paper missing responses"
        assert "200" in paper_schema["responses"], "/paper missing 200 response"
        print("   ✓ /paper schema OK")
        
        # Check scissors endpoint schema
        print("\n3. Checking /scissors endpoint schema...")
        scissors_schema = schema["paths"]["/scissors"]["post"]
        assert "responses" in scissors_schema, "/scissors missing responses"
        assert "200" in scissors_schema["responses"], "/scissors missing 200 response"
        print("   ✓ /scissors schema OK")
        
        # Check random endpoint schema
        print("\n4. Checking /random endpoint schema...")
        random_schema = schema["paths"]["/random"]["post"]
        assert "responses" in random_schema, "/random missing responses"
        assert "200" in random_schema["responses"], "/random missing 200 response"
        print("   ✓ /random schema OK")
        
        # Check shake endpoint schema
        print("\n5. Checking /shake endpoint schema...")
        shake_schema = schema["paths"]["/shake"]["post"]
        assert "responses" in shake_schema, "/shake missing responses"
        assert "200" in shake_schema["responses"], "/shake missing 200 response"
        print("   ✓ /shake schema OK")
        
        print("\n" + "=" * 60)
        print("✓ All schema tests passed!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ Schema test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Rock-Paper-Scissors API Test Suite")
    print("=" * 60)
    
    tests = [
        ("API Structure Test", test_api_structure),
        ("Endpoint Schema Test", test_endpoint_schemas),
    ]
    
    results = []
    for test_name, test_func in tests:
        results.append((test_name, test_func()))
    
    # Summary
    print("\n\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed! API is ready to use.")
        print("\nTo start the server, run:")
        print("  uv run uvicorn api:app --host 0.0.0.0 --port 8000 --reload")
        print("\nAPI documentation will be available at:")
        print("  http://localhost:8000/docs")
        print("=" * 60)
        return 0
    else:
        print("✗ Some tests failed. Please review the errors above.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())


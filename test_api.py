#!/usr/bin/env python3
"""
Simple test script to validate the SonarQube AI Advisor setup
"""
import asyncio
import httpx
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class APITester:
    def __init__(self):
        self.token = None
        self.base_url = BASE_URL
    
    async def test_health_check(self):
        """Test basic health check endpoint"""
        print("🏥 Testing health check...")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Health check passed: {data['status']}")
                    return True
                else:
                    print(f"❌ Health check failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_user_registration(self):
        """Test user registration"""
        print("👤 Testing user registration...")
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/auth/register",
                    json=user_data
                )
                if response.status_code == 201:
                    data = response.json()
                    print(f"✅ User registration successful: {data['username']}")
                    return True
                elif response.status_code == 400:
                    print("ℹ️ User already exists (this is normal)")
                    return True
                else:
                    print(f"❌ User registration failed: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
        except Exception as e:
            print(f"❌ User registration error: {e}")
            return False
    
    async def test_user_login(self):
        """Test user login and get token"""
        print("🔐 Testing user login...")
        login_data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/auth/login",
                    data=login_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                if response.status_code == 200:
                    data = response.json()
                    self.token = data["access_token"]
                    print("✅ User login successful")
                    return True
                else:
                    print(f"❌ User login failed: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
        except Exception as e:
            print(f"❌ User login error: {e}")
            return False
    
    async def test_protected_endpoint(self):
        """Test accessing a protected endpoint"""
        print("🛡️ Testing protected endpoint...")
        if not self.token:
            print("❌ No token available for testing")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/auth/me",
                    headers=headers
                )
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Protected endpoint access successful: {data['username']}")
                    return True
                else:
                    print(f"❌ Protected endpoint failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Protected endpoint error: {e}")
            return False
    
    async def test_sonarqube_projects(self):
        """Test SonarQube projects endpoint"""
        print("📊 Testing SonarQube projects endpoint...")
        if not self.token:
            print("❌ No token available for testing")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/analysis/sonarqube/projects",
                    headers=headers
                )
                if response.status_code == 200:
                    data = response.json()
                    project_count = len(data.get("projects", []))
                    print(f"✅ SonarQube projects accessible: {project_count} projects found")
                    return True
                elif response.status_code == 503:
                    print("⚠️ SonarQube server not accessible (check configuration)")
                    return False
                else:
                    print(f"❌ SonarQube projects failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ SonarQube projects error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting SonarQube AI Advisor API Tests")
        print("=" * 50)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("Protected Endpoint", self.test_protected_endpoint),
            ("SonarQube Projects", self.test_sonarqube_projects),
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n{test_name}:")
            result = await test_func()
            results.append((test_name, result))
        
        print("\n" + "=" * 50)
        print("📋 Test Results Summary:")
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} {test_name}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Your API is working correctly.")
        else:
            print("⚠️ Some tests failed. Check the configuration and ensure:")
            print("   - The API server is running")
            print("   - SonarQube server is accessible")
            print("   - Database is properly configured")
        
        return passed == total


async def main():
    """Main test function"""
    tester = APITester()
    await tester.run_all_tests()


if __name__ == "__main__":
    print("SonarQube AI Advisor - API Test Suite")
    print(f"Testing API at: {BASE_URL}")
    print("Make sure the API server is running before running this test!")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
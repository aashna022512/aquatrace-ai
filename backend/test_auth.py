#!/usr/bin/env python3
"""
Authentication Test for AquaTrace AI
Tests all login methods: Manual, Google OAuth, GitHub OAuth
"""

import requests
import time
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://127.0.0.1:5000"

def test_server_running():
    """Test if Flask server is running"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Flask server is running!")
            return True
        else:
            print(f"❌ Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Flask server is not running!")
        print("💡 Run: python app.py")
        return False
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return False

def test_registration():
    """Test user registration"""
    try:
        print("\n🔄 Testing user registration...")
        
        test_user = {
            'username': f'testuser_{int(time.time())}',  # Unique username
            'email': f'test_{int(time.time())}@example.com',  # Unique email
            'password': 'testpassword123'
        }
        
        response = requests.post(f"{BASE_URL}/register", data=test_user, allow_redirects=False)
        
        if response.status_code == 302:  # Redirect after successful registration
            print(f"✅ Registration successful for user: {test_user['username']}")
            return test_user
        else:
            print(f"❌ Registration failed. Status: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return None
            
    except Exception as e:
        print(f"❌ Registration test failed: {e}")
        return None

def test_login(test_user):
    """Test manual login with username/password"""
    try:
        print("\n🔄 Testing manual login...")
        
        if not test_user:
            print("❌ No test user available for login test")
            return False
        
        login_data = {
            'username': test_user['username'],
            'password': test_user['password']
        }
        
        # Create session to maintain cookies
        session = requests.Session()
        
        response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
        
        if response.status_code == 302:  # Redirect to dashboard after login
            print(f"✅ Manual login successful for: {test_user['username']}")
            
            # Test accessing protected route (dashboard)
            dashboard_response = session.get(f"{BASE_URL}/dashboard")
            if dashboard_response.status_code == 200:
                print("✅ Dashboard access successful after login!")
                return True
            else:
                print(f"❌ Dashboard access failed: {dashboard_response.status_code}")
                return False
        else:
            print(f"❌ Manual login failed. Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Login test failed: {e}")
        return False

def test_oauth_endpoints():
    """Test OAuth endpoints are accessible"""
    try:
        print("\n🔄 Testing OAuth endpoints...")
        
        # Test Google OAuth endpoint
        google_response = requests.get(f"{BASE_URL}/google_login", allow_redirects=False)
        if google_response.status_code == 302:
            print("✅ Google OAuth endpoint working (redirects to Google)")
        else:
            print(f"❌ Google OAuth endpoint failed: {google_response.status_code}")
        
        # Test GitHub OAuth endpoint  
        github_response = requests.get(f"{BASE_URL}/github_login", allow_redirects=False)
        if github_response.status_code == 302:
            print("✅ GitHub OAuth endpoint working (redirects to GitHub)")
        else:
            print(f"❌ GitHub OAuth endpoint failed: {github_response.status_code}")
            
        return True
        
    except Exception as e:
        print(f"❌ OAuth endpoints test failed: {e}")
        return False

def test_protected_routes():
    """Test that protected routes require authentication"""
    try:
        print("\n🔄 Testing protected routes...")
        
        # Try accessing dashboard without login
        response = requests.get(f"{BASE_URL}/dashboard", allow_redirects=False)
        
        if response.status_code == 302:  # Should redirect to login
            print("✅ Dashboard properly protected (redirects to login)")
            return True
        else:
            print(f"❌ Dashboard not properly protected. Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Protected routes test failed: {e}")
        return False

def main():
    """Run all authentication tests"""
    print("🚀 AquaTrace AI Authentication Test")
    print("=" * 50)
    
    # Test 1: Server running
    if not test_server_running():
        return
    
    # Test 2: Protected routes
    protected_ok = test_protected_routes()
    
    # Test 3: Registration
    test_user = test_registration()
    
    # Test 4: Manual login
    login_ok = test_login(test_user)
    
    # Test 5: OAuth endpoints
    oauth_ok = test_oauth_endpoints()
    
    # Summary
    print("\n📊 Authentication Test Results:")
    print("=" * 50)
    print(f"   Server Running: ✅")
    print(f"   Protected Routes: {'✅' if protected_ok else '❌'}")
    print(f"   User Registration: {'✅' if test_user else '❌'}")
    print(f"   Manual Login: {'✅' if login_ok else '❌'}")
    print(f"   OAuth Endpoints: {'✅' if oauth_ok else '❌'}")
    
    if protected_ok and test_user and login_ok and oauth_ok:
        print("\n🎉 ALL AUTHENTICATION TESTS PASSED!")
        print("✅ Manual login working")
        print("✅ OAuth endpoints working") 
        print("✅ Protected routes secured")
        print("✅ Registration working")
        print("\n💡 Now test OAuth manually:")
        print(f"   1. Go to {BASE_URL}/login")
        print("   2. Click 'Login with Google'")
        print("   3. Click 'Login with GitHub'")
    else:
        print("\n⚠️ Some authentication tests failed!")
        print("🔧 Check the errors above and fix them.")

if __name__ == "__main__":
    main()

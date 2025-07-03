#!/usr/bin/env python3
"""
Test WordPress connection with proper authentication
"""
import os
import requests
from requests.auth import HTTPBasicAuth

def test_wordpress_connection():
    # Get credentials from environment
    wp_url = os.getenv('WORDPRESS_URL', 'https://maquinanerd.com.br/wp-json/wp/v2/')
    wp_user = os.getenv('WORDPRESS_USER', 'Eduardo')
    wp_password = os.getenv('WORDPRESS_PASSWORD', '')
    
    # Fix URL if it doesn't end with the API path
    if not wp_url.endswith('/wp-json/wp/v2/'):
        if wp_url.endswith('/'):
            wp_url = wp_url + 'wp-json/wp/v2/'
        else:
            wp_url = wp_url + '/wp-json/wp/v2/'
    
    print(f"Testing WordPress connection...")
    print(f"URL: {wp_url}")
    print(f"User: {wp_user}")
    print(f"Password: {'*' * len(wp_password) if wp_password else 'NOT SET'}")
    
    # Test basic API access
    try:
        print("\n1. Testing basic API access (no auth)...")
        response = requests.get(f"{wp_url}", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✓ WordPress API is accessible")
        else:
            print(f"   ✗ API not accessible: {response.text[:200]}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test posts endpoint without auth
    try:
        print("\n2. Testing posts endpoint (no auth)...")
        response = requests.get(f"{wp_url}posts?per_page=1", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✓ Posts endpoint accessible without auth")
            data = response.json()
            print(f"   Found {len(data)} posts")
        else:
            print(f"   ✗ Posts endpoint issue: {response.text[:200]}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test with authentication
    if wp_password:
        try:
            print("\n3. Testing with authentication...")
            auth = HTTPBasicAuth(wp_user, wp_password)
            response = requests.get(f"{wp_url}posts?per_page=1", auth=auth, timeout=10)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✓ Authentication successful")
                data = response.json()
                print(f"   Found {len(data)} posts")
                if data:
                    print(f"   Latest post: {data[0].get('title', {}).get('rendered', 'No title')}")
            else:
                print(f"   ✗ Authentication failed: {response.text[:200]}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
    else:
        print("\n3. Skipping authentication test - no password set")
    
    # Test user endpoint
    if wp_password:
        try:
            print("\n4. Testing user permissions...")
            auth = HTTPBasicAuth(wp_user, wp_password)
            response = requests.get(f"{wp_url}users/me", auth=auth, timeout=10)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                user_data = response.json()
                print(f"   ✓ User authenticated: {user_data.get('name', 'Unknown')}")
                print(f"   Capabilities: {user_data.get('capabilities', {}).keys()}")
            else:
                print(f"   ✗ User authentication failed: {response.text[:200]}")
        except Exception as e:
            print(f"   ✗ Error: {e}")

if __name__ == "__main__":
    test_wordpress_connection()
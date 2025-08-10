#!/usr/bin/env python3
"""
Setup script for Hugging Face token and HLE dataset access
"""

import os
import requests
import json
from getpass import getpass

def setup_hf_token():
    """Set up Hugging Face token"""
    print("🔐 Hugging Face Token Setup")
    print("=" * 40)
    
    # Check if token already exists
    token = os.getenv('HF_TOKEN')
    if token:
        print(f"✅ HF_TOKEN already set: {token[:10]}...")
        return token
    
    print("To access the HLE dataset, you need a Hugging Face token.")
    print("\nSteps to get your token:")
    print("1. Go to https://huggingface.co")
    print("2. Sign in or create an account")
    print("3. Go to Settings → Access Tokens")
    print("4. Create a new token with 'Read' permissions")
    print("5. Copy the token")
    
    print("\n" + "=" * 40)
    
    # Get token from user
    token = getpass("Enter your Hugging Face token (input will be hidden): ")
    
    if not token:
        print("❌ No token provided. Cannot proceed.")
        return None
    
    # Test the token
    print("\n🔍 Testing token...")
    if test_hf_token(token):
        print("✅ Token is valid!")
        
        # Save token to environment
        save_token_to_env(token)
        return token
    else:
        print("❌ Token is invalid or doesn't have proper permissions.")
        return None

def test_hf_token(token):
    """Test if the HF token is valid"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test with a simple API call
    try:
        response = requests.get(
            "https://huggingface.co/api/whoami",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"✅ Authenticated as: {user_info.get('name', 'Unknown')}")
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing token: {e}")
        return False

def save_token_to_env(token):
    """Save token to environment file"""
    env_file = ".env"
    
    # Create or update .env file
    env_content = f"HF_TOKEN={token}\n"
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"✅ Token saved to {env_file}")
        print("⚠️  Remember to add .env to your .gitignore file!")
    except Exception as e:
        print(f"❌ Error saving token: {e}")

def test_hle_access(token):
    """Test access to HLE dataset"""
    print("\n🔍 Testing HLE Dataset Access")
    print("=" * 40)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Try to access HLE dataset
    url = "https://datasets-server.huggingface.co/first-rows?dataset=cais%2Fhle&config=default&split=test"
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Successfully accessed HLE dataset!")
            
            # Show sample data
            if 'rows' in data and data['rows']:
                print(f"\n📊 Dataset Info:")
                print(f"Total rows: {data.get('num_rows_total', 'Unknown')}")
                print(f"Columns: {list(data.get('features', {}).keys())}")
                
                # Show first question
                first_row = data['rows'][0]
                if 'row' in first_row:
                    row_data = first_row['row']
                    print(f"\n🎯 Sample Question:")
                    print(f"ID: {row_data.get('id', 'N/A')}")
                    print(f"Question: {row_data.get('question', 'N/A')[:100]}...")
                    print(f"Subject: {row_data.get('subject', 'N/A')}")
                    print(f"Difficulty: {row_data.get('difficulty', 'N/A')}")
                    
                return True
            else:
                print("⚠️  No data rows found in response")
                return False
                
        elif response.status_code == 403:
            print("❌ Access denied. You need to request access to the HLE dataset.")
            print("Visit: https://huggingface.co/datasets/cais/hle")
            print("Click 'Request access' and wait for approval.")
            return False
            
        else:
            print(f"❌ Error accessing dataset: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing HLE access: {e}")
        return False

def main():
    """Main setup function"""
    print("🧠 HLE Dataset Access Setup")
    print("=" * 50)
    
    # Step 1: Setup token
    token = setup_hf_token()
    if not token:
        return
    
    # Step 2: Test HLE access
    if test_hle_access(token):
        print("\n🎉 Setup complete! You can now access the HLE dataset.")
        print("\nTo use the real HLE questions in your quiz app:")
        print("1. Update hle_quiz_integration.py to use use_sample=False")
        print("2. The app will automatically use the real dataset")
    else:
        print("\n⚠️  Setup incomplete. You need to request access to the HLE dataset.")
        print("Visit: https://huggingface.co/datasets/cais/hle")

if __name__ == "__main__":
    main()

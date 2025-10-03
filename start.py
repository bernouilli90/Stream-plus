#!/usr/bin/env python3
"""
Stream Plus - Quick application startup

This script verifies configuration and starts the Flask application.
"""

import os
import sys
from pathlib import Path

def check_requirements():
    """Verify that requirements.txt is installed"""
    try:
        import flask
        import requests
        from dotenv import load_dotenv
        print("✓ Dependencies installed correctly")
        return True
    except ImportError as e:
        print(f"✗ Error: Missing dependency - {e}")
        print("Run: pip install -r requirements.txt")
        return False

def check_env_file():
    """Verify that the .env file exists"""
    env_file = Path('.env')
    if env_file.exists():
        print("✓ .env file found")
        return True
    else:
        print("✗ .env file not found")
        print("Copy .env.example to .env and configure the variables")
        return False

def check_dispatcharr_config():
    """Verify Dispatcharr configuration"""
    from dotenv import load_dotenv
    load_dotenv()
    
    api_url = os.getenv('DISPATCHARR_API_URL')
    api_key = os.getenv('DISPATCHARR_API_KEY')
    
    if not api_url:
        print("✗ DISPATCHARR_API_URL not configured")
        return False
    
    if not api_key:
        print("⚠ DISPATCHARR_API_KEY not configured (optional)")
    
    print(f"✓ API URL configured: {api_url}")
    return True

def main():
    """Main function"""
    print("Stream Plus - Configuration verification\n")
    
    # Verify dependencies
    if not check_requirements():
        sys.exit(1)
    
    # Verify .env file
    if not check_env_file():
        sys.exit(1)
    
    # Verify Dispatcharr configuration
    if not check_dispatcharr_config():
        sys.exit(1)
    
    print("\n✓ Configuration verified successfully")
    print("Starting Stream Plus...\n")
    
    # Import and run the application
    try:
        from app import app
        port = int(os.getenv('PORT', 5000))
        debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        
        print(f"Stream Plus started at http://localhost:{port}")
        print("Press Ctrl+C to stop\n")
        
        app.run(host='0.0.0.0', port=port, debug=debug)
        
    except Exception as e:
        print(f"✗ Error starting the application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
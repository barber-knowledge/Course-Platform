"""
Modular Course Platform - Application Entry Point
"""
import sys
import time
from flask import cli
from app import create_app
from test_db_connection import test_database_connection
from config import Config

# Disable Flask's messages about running a development server
cli.show_server_banner = lambda *args: None

if __name__ == "__main__":
    # Test database connection before starting the server
    print("Testing database connection...")
    
    # Try to connect up to 3 times with 2 second delay between attempts
    connected = False
    for attempt in range(3):
        if attempt > 0:
            print(f"Retrying connection (attempt {attempt+1}/3)...")
            time.sleep(2)
        
        if test_database_connection():
            connected = True
            break
    
    if not connected:
        print(f"[ERROR] Failed to connect to database at {Config.DB_HOST}:{Config.DB_PORT}")
        print("Please check your database settings in config.py")
        print("Exiting...")
        sys.exit(1)
    
    # Create and run the Flask application
    app = create_app()
    print(f"[SUCCESS] Starting Flask server with database at {Config.DB_HOST}")
    app.run(debug=True)
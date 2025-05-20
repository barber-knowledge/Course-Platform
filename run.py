"""
Modular Course Platform - Application Entry Point
"""
import sys
import time
import argparse
from flask import cli
from app import create_app
from test_db_connection import test_database_connection
from config import Config

# Disable Flask's messages about running a development server
cli.show_server_banner = lambda *args: None

def reset_course_data():
    """Reset all course completion data in the database."""
    from app import db
    from app.models import User, Course, CourseProgress  # Import your actual models
    
    try:
        print("Resetting course completion data...")
        # This implementation depends on your actual data model
        # The following is a generic approach - modify according to your schema
        db.session.query(CourseProgress).delete()
        db.session.commit()
        print("[SUCCESS] Course completion data has been reset.")
    except Exception as e:
        print(f"[ERROR] Failed to reset course data: {str(e)}")
        db.session.rollback()
        return False
    return True

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Modular Course Platform")
    parser.add_argument('--reset', action='store_true', help='Reset all course completion data')
    args = parser.parse_args()
    
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
    
    # Create the Flask application
    app = create_app()
    
    # Reset course data if requested
    if args.reset:
        with app.app_context():
            if not reset_course_data():
                sys.exit(1)
    
    print(f"[SUCCESS] Starting Flask server with database at {Config.DB_HOST}")
    app.run(debug=True)
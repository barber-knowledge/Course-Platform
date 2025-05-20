"""
Database initialization script for Modular Course Platform

This script creates all database tables defined in the ORM models
"""
from app import create_app, db
from app.models import User, Course, Video, Quiz, PlatformConfig

# Main initialization
if __name__ == "__main__":
    # Create Flask app instance
    app = create_app()
    print("Attempting to connect to remote database...")
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("Database tables created successfully.")
            
            # Check if a PlatformConfig entry exists, create one if not
            platform_config = PlatformConfig.query.first()
            if not platform_config:
                platform_config = PlatformConfig(
                    platform_name="Modular Course Platform",
                    primary_color="#0d6efd",
                    secondary_color="#6c757d",
                    setup_complete=False
                )
                db.session.add(platform_config)
                db.session.commit()
                print("Default platform configuration created.")
            
            print("Database initialization complete.")
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            print("Please ensure your database credentials are correct and the database exists.")
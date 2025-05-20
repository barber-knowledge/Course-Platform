"""
Simple script to create the certificate_settings table
"""
import os
import sys

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from app import create_app, db
from app.models import CertificateSettings

# Create a Flask app context
app = create_app()

with app.app_context():
    print("Creating certificate_settings table...")
    
    # Check if table exists by querying for it
    inspector = db.inspect(db.engine)
    table_exists = 'certificate_settings' in inspector.get_table_names()
    
    if not table_exists:
        print("Table does not exist, creating it...")
        # Create just this table
        CertificateSettings.__table__.create(db.engine)
        print("Table created successfully")
        
        # Create default settings
        settings = CertificateSettings(
            background_color="#FFFFFF",
            border_color="#294767",
            text_color="#000000",
            certificate_title="CERTIFICATE OF COMPLETION",
            certificate_text="has successfully completed the course",
            footer_text="",
            instructor_name="Course Instructor"
        )
        
        db.session.add(settings)
        db.session.commit()
        print("Default settings added to the table")
    else:
        print("Table already exists")
    
    print("Migration completed")
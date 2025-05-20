"""
Create the certificate_settings table using SQLAlchemy ORM
"""
from flask import Flask
import sys
import os
from datetime import datetime

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the Flask application and database
from app import create_app, db
from app.models import CertificateSettings

def create_certificate_settings_table():
    """
    Create the certificate_settings table using SQLAlchemy ORM
    and insert default values
    """
    app = create_app()
    
    with app.app_context():
        # Create the table
        print("Creating certificate_settings table...")
        db.create_all()
        
        # Check if there are any settings already
        existing_settings = CertificateSettings.query.first()
        
        if not existing_settings:
            print("Inserting default certificate settings...")
            default_settings = CertificateSettings(
                background_color='#FFFFFF',
                border_color='#294767',
                text_color='#000000',
                certificate_title='CERTIFICATE OF COMPLETION',
                certificate_text='has successfully completed the course',
                footer_text='',
                instructor_name='Course Instructor'
            )
            
            db.session.add(default_settings)
            db.session.commit()
            print("Default certificate settings created successfully.")
        else:
            print("Certificate settings already exist.")

if __name__ == '__main__':
    try:
        create_certificate_settings_table()
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Error during migration: {e}")
        sys.exit(1)
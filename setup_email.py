"""
Initialize the database and configure email settings
"""

import os
import sys
from flask import Flask
from app import db, create_app
from app.models import User, PlatformConfig, EmailTemplate

# SMTP configuration values
SMTP_CONFIG = {
    'smtp_server': 'smtp.mailgun.org',
    'smtp_port': 587,  # Using TLS port
    'smtp_username': 'example@mail.example.com',
    'smtp_password': 'your-mailgun-api-key-here',
    'smtp_use_tls': True,
    'smtp_use_ssl': False,
    'smtp_default_sender': 'example@mail.example.com',
    'smtp_enabled': True
}

def setup_database_and_email():
    """Initialize database and configure email settings"""
    app = create_app()
    
    with app.app_context():
        # Create database tables
        try:
            db.create_all()
            print("Database tables created successfully!")
        except Exception as e:
            print(f"Error creating database tables: {str(e)}")
            return
        
        # Configure email settings
        try:
            config = PlatformConfig.get_config()
            
            # Update SMTP settings
            for key, value in SMTP_CONFIG.items():
                setattr(config, key, value)
            
            db.session.commit()
            print("\nSMTP settings configured successfully!")
            print(f"Server: {config.smtp_server}")
            print(f"Port: {config.smtp_port}")
            print(f"Username: {config.smtp_username}")
            print(f"TLS: {config.smtp_use_tls}")
            print(f"SSL: {config.smtp_use_ssl}")
            print(f"Default sender: {config.smtp_default_sender}")
            print(f"Email sending enabled: {config.smtp_enabled}")
            
            # Initialize default email templates
            EmailTemplate.init_default_templates()
            print("\nDefault email templates initialized!")
            templates = EmailTemplate.query.all()
            for template in templates:
                print(f"- {template.name} ({template.template_key})")
                
        except Exception as e:
            print(f"Error configuring email settings: {str(e)}")
            return

if __name__ == "__main__":
    setup_database_and_email()
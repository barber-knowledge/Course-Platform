"""
Utility script to configure email settings for the platform
This script sets up the SMTP settings in the database so you don't have to enter them manually.
"""

import os
import sys
from flask import Flask
from app import db
from app.models import PlatformConfig

# Configure the Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

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

def configure_smtp():
    """Configure SMTP settings in the database"""
    with app.app_context():
        config = PlatformConfig.get_config()
        
        # Update SMTP settings
        for key, value in SMTP_CONFIG.items():
            setattr(config, key, value)
        
        db.session.commit()
        print("SMTP settings configured successfully!")
        print(f"Server: {config.smtp_server}")
        print(f"Port: {config.smtp_port}")
        print(f"Username: {config.smtp_username}")
        print(f"TLS: {config.smtp_use_tls}")
        print(f"SSL: {config.smtp_use_ssl}")
        print(f"Default sender: {config.smtp_default_sender}")
        print(f"Email sending enabled: {config.smtp_enabled}")

if __name__ == "__main__":
    configure_smtp()
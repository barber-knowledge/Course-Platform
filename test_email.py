"""
A test script to verify email functionality in the modular course platform

This script sends a test email using the database configuration settings
to verify that the email system is working correctly.
"""
import os
import sys
import logging
from flask import Flask
from app import create_app
from app.models import PlatformConfig, db
from app.utils.email import EmailService
from flask_mail import Message
from app import mail

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_email_settings():
    """Verify the email settings in the database"""
    app = create_app()
    
    with app.app_context():
        # Get the platform configuration
        config = PlatformConfig.get_config()
        
        # Display current email settings
        logger.info("Current email configuration:")
        logger.info(f"SMTP Server: {config.smtp_server}")
        logger.info(f"SMTP Port: {config.smtp_port}")
        logger.info(f"SMTP Username: {config.smtp_username}")
        logger.info(f"SMTP Password: {'*' * 8 if config.smtp_password else 'Not set'}")
        logger.info(f"Default Sender: {config.smtp_default_sender}")
        logger.info(f"SMTP Enabled: {config.smtp_enabled}")
        logger.info(f"TLS Enabled: {config.smtp_use_tls}")
        logger.info(f"SSL Enabled: {config.smtp_use_ssl}")
        
        # Get the Flask-Mail settings from the app config
        logger.info("\nFlask-Mail configuration:")
        for key in app.config:
            if key.startswith('MAIL_'):
                logger.info(f"{key}: {app.config[key]}")
        
        # Check if SMTP is enabled
        if not config.smtp_enabled:
            logger.warning("SMTP is disabled in the database. Enabling it for testing...")
            config.smtp_enabled = True
            db.session.commit()
        
        # If needed, update with Mailgun settings
        if not config.smtp_server:
            logger.warning("No SMTP server configured. Updating with Mailgun settings...")
            config.smtp_server = 'smtp.mailgun.org'
            config.smtp_port = 587
            config.smtp_username = 'example@mail.example.com'
            config.smtp_password = 'your-mailgun-api-key-here'
            config.smtp_use_tls = True
            config.smtp_use_ssl = False
            config.smtp_default_sender = 'example@mail.example.com'
            config.smtp_enabled = True
            db.session.commit()
            logger.info("Email configuration updated with Mailgun settings")
            
            # Restart the app to apply the new configuration
            logger.info("Restarting app to apply new configuration...")
            app = create_app()
        
        return config

def send_test_email(recipient_email):
    """Send a test email using the configured settings"""
    app = create_app()
    
    with app.app_context():
        try:
            # Verify email settings
            config = verify_email_settings()
            
            # Create a test message
            logger.info(f"Sending test email to {recipient_email}...")
            
            # Create message directly with Flask-Mail
            msg = Message(
                subject='Test Email from Modular Course Platform',
                recipients=[recipient_email],
                sender=config.smtp_default_sender,
                body='This is a test email to verify that the email functionality is working correctly.',
                html='<h1>Test Email</h1><p>This is a test email to verify that the email functionality is working correctly.</p>'
            )
            
            # Send the email
            mail.send(msg)
            logger.info("Test email sent successfully!")
            
            return True
        except Exception as e:
            logger.error(f"Failed to send test email: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_email.py <recipient_email>")
        sys.exit(1)
    
    recipient_email = sys.argv[1]
    if send_test_email(recipient_email):
        print(f"Test email sent successfully to {recipient_email}!")
    else:
        print("Failed to send test email. Check the logs for details.")
        sys.exit(1)
"""
Script to setup the certificate email template and verify email configuration
"""
import os
import sys
from flask import Flask
from app import create_app
from app.models import EmailTemplate, PlatformConfig, db
from app.utils.email import EmailService
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_certificate_template():
    """Setup the certificate email template"""
    app = create_app()
    
    with app.app_context():
        # Check if template exists
        template = EmailTemplate.query.filter_by(template_key='certificate_issued').first()
        if not template:
            logger.info("Creating certificate_issued email template")
            template = EmailTemplate(
                name='Certificate Issued Notification',
                subject='Your Certificate for {{ course.title }} is Ready',
                body_html='''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1>Your Certificate is Ready!</h1>
                    <p>Hello {{ user.name }},</p>
                    <p>Congratulations on completing <strong>{{ course.title }}</strong>! Your certificate of completion is now ready.</p>
                    <p>You can view and download your certificate using the links below:</p>
                    <p>
                        <a href="{{ certificate_view_url }}" style="display: inline-block; background-color: {{ config.primary_color }}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">View Certificate</a>
                        <a href="{{ certificate_download_url }}" style="display: inline-block; background-color: {{ config.primary_color }}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Download Certificate</a>
                    </p>
                    <p>Your certificate has also been attached to this email for your convenience.</p>
                    <p>Congratulations again on your achievement!</p>
                    <p>Best regards,<br>The {{ config.platform_name }} Team</p>
                </div>
                ''',
                body_text='''
                Your Certificate is Ready!
                
                Hello {{ user.name }},
                
                Congratulations on completing {{ course.title }}! Your certificate of completion is now ready.
                
                You can view your certificate at: {{ certificate_view_url }}
                You can download your certificate at: {{ certificate_download_url }}
                
                Your certificate has also been attached to this email for your convenience.
                
                Congratulations again on your achievement!
                
                Best regards,
                The {{ config.platform_name }} Team
                ''',
                description='Email sent to users when their course certificate is generated',
                template_key='certificate_issued',
                is_active=True
            )
            db.session.add(template)
            db.session.commit()
            logger.info("Certificate email template created successfully")
        else:
            logger.info("Certificate email template already exists")
        
        # Verify email configuration
        config = PlatformConfig.get_config()
        logger.info("Current email configuration:")
        logger.info(f"SMTP Server: {config.smtp_server}")
        logger.info(f"SMTP Port: {config.smtp_port}")
        logger.info(f"SMTP Username: {config.smtp_username}")
        logger.info(f"SMTP Password: {'*' * 8 if config.smtp_password else 'Not set'}")
        logger.info(f"Default Sender: {config.smtp_default_sender}")
        logger.info(f"SMTP Enabled: {config.smtp_enabled}")
        logger.info(f"TLS Enabled: {config.smtp_use_tls}")
        logger.info(f"SSL Enabled: {config.smtp_use_ssl}")
        
        # Update email configuration from Mailgun settings
        if not config.smtp_enabled or not config.smtp_server:
            logger.info("Email is not configured or disabled. Configuring with Mailgun settings...")
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
        
        return True

if __name__ == "__main__":
    setup_certificate_template()
    print("Certificate email template setup complete!")
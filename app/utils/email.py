"""
Email utility service for sending templated emails
"""
import logging
import os
from flask import current_app, render_template_string, url_for
from threading import Thread
from flask_mail import Message
from app import mail, db
from app.models import EmailTemplate, PlatformConfig

class EmailService:
    """
    Service class for sending emails with templates from the database
    """
    
    @staticmethod
    def send_email(subject, recipients, html_body, text_body=None, sender=None, attachments=None, sync=False):
        """
        Send an email using Flask-Mail
        
        Args:
            subject (str): Email subject
            recipients (list): List of recipient email addresses
            html_body (str): HTML content of the email
            text_body (str, optional): Plain text content of the email
            sender (str, optional): Sender email address, defaults to config default_sender
            attachments (list, optional): List of (filename, mimetype, data) tuples
            sync (bool, optional): If True, send synchronously, otherwise in background thread
            
        Returns:
            bool: True if the email was sent successfully, False otherwise
        """
        try:
            # Get platform config to use default sender if none provided
            config = PlatformConfig.get_config()
            if not sender and config.smtp_default_sender:
                sender = config.smtp_default_sender
                
            # Check if email sending is enabled
            if not config.smtp_enabled:
                current_app.logger.warning("Email sending is disabled in platform configuration")
                return False
                
            # Log email details for debugging
            current_app.logger.info(f"Sending email to {recipients} using SMTP server: {config.smtp_server}:{config.smtp_port}")
            current_app.logger.info(f"SMTP auth: {config.smtp_username}")
            
            msg = Message(subject, recipients=recipients, sender=sender)
            msg.html = html_body
            
            if text_body:
                msg.body = text_body
                
            # Add attachments if any
            if attachments:
                for attachment in attachments:
                    filename, mimetype, data = attachment
                    msg.attach(filename=filename, content_type=mimetype, data=data)
                    current_app.logger.info(f"Attached file: {filename} ({mimetype})")
            
            # Send email synchronously or in background thread
            if sync:
                mail.send(msg)
                current_app.logger.info("Email sent synchronously")
            else:
                Thread(target=_send_email_async, args=(current_app._get_current_object(), msg)).start()
                current_app.logger.info("Email sent asynchronously")
                
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to send email: {str(e)}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            return False
    
    @classmethod
    def send_template_email(cls, template_key, recipients, context=None, sync=False, attachments=None):
        """
        Send an email using a template from the database
        
        Args:
            template_key (str): The template key to use
            recipients (list): List of recipient email addresses
            context (dict, optional): Context variables for template rendering
            sync (bool, optional): If True, send synchronously
            attachments (list, optional): List of (filename, mimetype, data) tuples
            
        Returns:
            bool: True if the email was sent successfully, False otherwise
        """
        try:
            # Load template from database
            template = EmailTemplate.get_template(template_key)
            if not template or not template.is_active:
                current_app.logger.warning(f"Email template '{template_key}' not found or inactive")
                return False
                
            # Prepare context for template rendering
            if context is None:
                context = {}
                
            # Add global context variables
            config = PlatformConfig.get_config()
            context['config'] = config
            
            # Render templates with context
            subject = render_template_string(template.subject, **context)
            html_body = render_template_string(template.body_html, **context)
            
            text_body = None
            if template.body_text:
                text_body = render_template_string(template.body_text, **context)
                
            # Send the email
            return cls.send_email(
                subject=subject,
                recipients=recipients,
                html_body=html_body,
                text_body=text_body,
                attachments=attachments,
                sync=sync
            )
            
        except Exception as e:
            current_app.logger.error(f"Failed to send template email: {str(e)}")
            return False
    
    @classmethod
    def send_user_registration_email(cls, user):
        """
        Send welcome email to a newly registered user
        
        Args:
            user: The user model instance
            
        Returns:
            bool: True if the email was sent successfully, False otherwise
        """
        context = {
            'user': user,
            'login_url': url_for('auth.login', _external=True)
        }
        
        return cls.send_template_email(
            template_key='user_registration',
            recipients=[user.email],
            context=context
        )
    
    @classmethod
    def send_course_enrollment_email(cls, user, course):
        """
        Send course enrollment confirmation email
        
        Args:
            user: The user model instance
            course: The course model instance
            
        Returns:
            bool: True if the email was sent successfully, False otherwise
        """
        context = {
            'user': user,
            'course': course,
            'course_url': url_for('courses.view', course_id=course.id, _external=True)
        }
        
        return cls.send_template_email(
            template_key='course_enrollment',
            recipients=[user.email],
            context=context
        )
    
    @classmethod
    def send_course_completion_email(cls, user, course, certificate=None):
        """
        Send course completion congratulations email
        
        Args:
            user: The user model instance
            course: The course model instance
            certificate: Optional certificate model instance
            
        Returns:
            bool: True if the email was sent successfully, False otherwise
        """
        context = {
            'user': user,
            'course': course
        }
        
        # Add certificate URL if available
        if certificate:
            context['certificate_url'] = url_for(
                'certificates.download', 
                certificate_id=certificate.certificate_id, 
                _external=True
            )
        
        return cls.send_template_email(
            template_key='course_completion',
            recipients=[user.email],
            context=context
        )
    
    @classmethod
    def send_quiz_results_email(cls, user, quiz, quiz_attempt):
        """
        Send quiz results email
        
        Args:
            user: The user model instance
            quiz: The quiz model instance
            quiz_attempt: The quiz attempt model instance
            
        Returns:
            bool: True if the email was sent successfully, False otherwise
        """
        context = {
            'user': user,
            'quiz': quiz,
            'quiz_attempt': quiz_attempt,
            'quiz_results_url': url_for(
                'quizzes.results', 
                quiz_id=quiz.id, 
                attempt_id=quiz_attempt.id, 
                _external=True
            )
        }
        
        return cls.send_template_email(
            template_key='quiz_completion',
            recipients=[user.email],
            context=context
        )
    
    @classmethod
    def send_product_purchase_email(cls, user, product, purchase):
        """
        Send product purchase confirmation email
        
        Args:
            user: The user model instance
            product: The product model instance
            purchase: The product purchase model instance
            
        Returns:
            bool: True if the email was sent successfully, False otherwise
        """
        context = {
            'user': user,
            'product': product,
            'purchase': purchase
        }
        
        # Add download URL if product has one
        if product.download_link:
            context['download_url'] = url_for(
                'products.download', 
                product_id=product.id, 
                _external=True
            )
        
        return cls.send_template_email(
            template_key='product_purchase',
            recipients=[user.email],
            context=context
        )
    
    @classmethod
    def send_password_reset_email(cls, user):
        """
        Send password reset email with token
        
        Args:
            user: The user model instance
            
        Returns:
            bool: True if the email was sent successfully, False otherwise
        """
        token = user.generate_reset_token()
        
        context = {
            'user': user,
            'reset_url': url_for('auth.reset_password', token=token, _external=True)
        }
        
        return cls.send_template_email(
            template_key='password_reset',
            recipients=[user.email],
            context=context
        )
    
    @classmethod
    def send_certificate_email(cls, user, course, certificate):
        """
        Send certificate email with PDF attachment
        
        Args:
            user: The user model instance
            course: The course model instance
            certificate: The certificate model instance
            
        Returns:
            bool: True if the email was sent successfully, False otherwise
        """
        try:
            # Check if email sending is enabled in platform config
            config = PlatformConfig.get_config()
            if not config.smtp_enabled:
                current_app.logger.warning(f"Email sending is disabled. Certificate email not sent to {user.email}")
                return False
                
            # Create context for email template
            context = {
                'user': user,
                'course': course,
                'certificate': certificate,
                'certificate_view_url': url_for('certificates.view', course_id=course.id, _external=True),
                'certificate_download_url': url_for('certificates.download', certificate_id=certificate.certificate_id, _external=True)
            }
            
            # Prepare certificate PDF attachment
            certificate_path = os.path.join(current_app.static_folder, certificate.file_path)
            attachments = None
            
            if os.path.exists(certificate_path):
                with open(certificate_path, 'rb') as pdf_file:
                    pdf_data = pdf_file.read()
                    filename = f"certificate_{course.title}_{user.name}.pdf"
                    attachments = [(filename, 'application/pdf', pdf_data)]
                    current_app.logger.info(f"Certificate PDF attached to email for {user.email}")
            else:
                current_app.logger.warning(f"Certificate PDF not found at {certificate_path}")
            
            return cls.send_template_email(
                template_key='certificate_issued',
                recipients=[user.email],
                context=context,
                attachments=attachments
            )
        except Exception as e:
            current_app.logger.error(f"Failed to send certificate email: {str(e)}")
            return False
    
    @classmethod
    def init_certificate_email_template(cls):
        """
        Create the certificate email template if it doesn't exist
        """
        try:
            with current_app.app_context():
                # Check if template exists
                template = EmailTemplate.query.filter_by(template_key='certificate_issued').first()
                if not template:
                    current_app.logger.info("Creating certificate_issued email template")
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
                        body_text=''':
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
                    current_app.logger.info("Certificate email template created successfully")
                    return True
                else:
                    current_app.logger.info("Certificate email template already exists")
                    return False
        except Exception as e:
            current_app.logger.error(f"Error creating certificate email template: {str(e)}")
            return False


def _send_email_async(app, msg):
    """
    Send email asynchronously in a separate thread
    """
    with app.app_context():
        try:
            mail.send(msg)
            app.logger.info(f"Async email sent successfully to {msg.recipients}")
        except Exception as e:
            app.logger.error(f"Failed to send email asynchronously: {str(e)}")
            import traceback
            app.logger.error(traceback.format_exc())
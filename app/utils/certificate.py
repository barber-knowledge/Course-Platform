"""
Certificate utility functions
"""
import os
import uuid
import datetime
from datetime import timezone
import hashlib
from io import BytesIO
from flask import current_app, url_for, render_template
from app.models import Certificate, Course, User, CertificateSettings
from app import db
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Image
from PIL import Image as PILImage

# Helper function to get current UTC time
def get_utc_now():
    """Return current UTC datetime - replacement for datetime.utcnow"""
    return datetime.datetime.now(timezone.utc)

def generate_certificate(user_id, course_id):
    """
    Generate a certificate for a user who has completed a course
    
    Args:
        user_id (int): The ID of the user
        course_id (int): The ID of the course
        
    Returns:
        Certificate: The newly created certificate or None if failed
    """
    # Check if certificate already exists
    existing_certificate = Certificate.query.filter_by(
        user_id=user_id, 
        course_id=course_id
    ).first()
    
    if existing_certificate:
        # Check if the PDF file exists, if not, regenerate it
        pdf_path = os.path.join(current_app.static_folder, existing_certificate.file_path)
        if not os.path.exists(pdf_path):
            try:
                user = User.query.get(user_id)
                course = Course.query.get(course_id)
                create_certificate_pdf(existing_certificate, user, course, pdf_path)
                current_app.logger.info(f"Regenerated missing PDF for existing certificate: {existing_certificate.certificate_id}")
            except Exception as e:
                current_app.logger.error(f"Failed to regenerate PDF for certificate {existing_certificate.certificate_id}: {str(e)}")
        return existing_certificate
    
    # Get the user and course
    user = User.query.get(user_id)
    course = Course.query.get(course_id)
    
    if not user or not course:
        current_app.logger.error(f"Failed to generate certificate: User {user_id} or Course {course_id} not found")
        return None
    
    # Make sure the course has certificates enabled
    if not course.has_certificate:
        current_app.logger.info(f"Course {course.title} does not have certificates enabled")
        return None
    
    # Generate a unique certificate ID
    certificate_id = str(uuid.uuid4())
    
    # Create the certificates directory if it doesn't exist
    certificates_dir = os.path.join(current_app.static_folder, 'uploads', 'certificates')
    os.makedirs(certificates_dir, exist_ok=True)
    
    # Generate file path for the certificate
    file_path = f"uploads/certificates/certificate_{certificate_id}.pdf"
    full_file_path = os.path.join(current_app.static_folder, file_path)
    
    # Create the certificate record
    certificate = Certificate(
        user_id=user_id,
        course_id=course_id,
        certificate_id=certificate_id,
        file_path=file_path,
        issue_date=get_utc_now()
    )
    
    try:
        # Add to database
        db.session.add(certificate)
        db.session.commit()
        current_app.logger.info(f"Certificate generated for user {user.email} for course {course.title}")
        
        # Generate PDF certificate
        create_certificate_pdf(certificate, user, course, full_file_path)
        
        # Verify the file was created
        if not os.path.exists(full_file_path):
            current_app.logger.error(f"Certificate PDF file was not created at {full_file_path}")
            raise Exception("Certificate PDF file was not created")
        else:
            current_app.logger.info(f"Certificate PDF file successfully created at {full_file_path}")
        
        return certificate
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to generate certificate: {str(e)}")
        return None

def create_certificate_pdf(certificate, user, course, output_path):
    """
    Create a PDF certificate using ReportLab
    
    Args:
        certificate (Certificate): The certificate object
        user (User): The user object
        course (Course): The course object
        output_path (str): The path to save the PDF to
    """
    try:
        # Get certificate settings from the database
        settings = CertificateSettings.get_settings()
        
        # Make sure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Set up the PDF canvas with landscape orientation
        c = canvas.Canvas(output_path, pagesize=landscape(letter))
        width, height = landscape(letter)
        
        # Parse colors from hex to ReportLab color objects
        def hex_to_rgb(hex_color):
            try:
                hex_color = hex_color.lstrip('#')
                return tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))
            except Exception as e:
                current_app.logger.error(f"Error parsing color {hex_color}: {str(e)}")
                return (0, 0, 0)  # Default to black in case of error
        
        # Handle colors with error checking
        try:
            bg_color = colors.Color(*hex_to_rgb(settings.background_color))
        except:
            current_app.logger.warning("Invalid background color, using default")
            bg_color = colors.white
            
        try:
            border_color = colors.Color(*hex_to_rgb(settings.border_color))
        except:
            current_app.logger.warning("Invalid border color, using default")
            border_color = colors.black
            
        try:
            text_color = colors.Color(*hex_to_rgb(settings.text_color))
        except:
            current_app.logger.warning("Invalid text color, using default")
            text_color = colors.black
        
        # Set background color
        c.setFillColor(bg_color)
        c.rect(0, 0, width, height, fill=True)
        
        # Draw border
        c.setStrokeColor(border_color)
        c.setLineWidth(3)
        c.rect(0.5*inch, 0.5*inch, width-inch, height-inch)
        
        # Add watermark
        c.setFillColor(colors.Color(0.78, 0.78, 0.78, 0.3))  # Light gray with 30% opacity
        c.setFont("Helvetica", 80)
        c.saveState()
        c.translate(width/2, height/2)
        c.rotate(-30)
        c.drawCentredString(0, 0, "CERTIFIED")
        c.restoreState()
        
        # Add platform logo/name at top
        platform_name = current_app.config.get('PLATFORM_NAME', 'Learning Platform')
        c.setFillColor(text_color)
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width/2, height-1.5*inch, platform_name)
        
        # Add logo if available
        if settings.logo_image:
            try:
                logo_path = os.path.join(current_app.static_folder, settings.logo_image)
                if os.path.exists(logo_path):
                    logo = PILImage.open(logo_path)
                    logo_width, logo_height = logo.size
                    # Scale logo to fit
                    max_logo_width = 2 * inch
                    max_logo_height = 1.5 * inch
                    scale_factor = min(max_logo_width/logo_width, max_logo_height/logo_height)
                    logo_width *= scale_factor
                    logo_height *= scale_factor
                    c.drawImage(logo_path, (width - logo_width)/2, height-2*inch, width=logo_width, height=logo_height)
                else:
                    current_app.logger.warning(f"Logo image not found at {logo_path}")
            except Exception as e:
                current_app.logger.error(f"Error adding logo to certificate: {str(e)}")
        
        # Add certificate title
        c.setFillColor(text_color)
        c.setFont("Helvetica-Bold", 36)
        c.drawCentredString(width/2, height-2.5*inch, settings.certificate_title or "CERTIFICATE OF COMPLETION")
        
        # Add user name
        c.setFont("Helvetica-Bold", 32)
        c.drawCentredString(width/2, height/2, user.name)
        
        # Add certificate text
        c.setFont("Helvetica", 18)
        c.drawCentredString(width/2, height/2-0.5*inch, settings.certificate_text or "has successfully completed the course")
        
        # Add course name
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width/2, height/2-1.1*inch, course.title)
        
        # Add issue date
        issue_date = certificate.issue_date.strftime("%B %d, %Y")
        c.setFont("Helvetica", 14)
        c.drawCentredString(width/2, height/2-1.6*inch, f"Issued on {issue_date}")
        
        # Add verification text
        verify_url = url_for('certificates.verify', certificate_id=certificate.certificate_id, _external=True)
        c.setFont("Helvetica", 10)
        c.drawCentredString(width/2, 1.2*inch, f"To verify this certificate, please visit:")
        c.drawCentredString(width/2, 0.9*inch, verify_url)
        
        # Add signature
        c.line(width/2-1.5*inch, 2.5*inch, width/2+1.5*inch, 2.5*inch)
        
        # Add signature image if available
        if settings.signature_image:
            try:
                signature_path = os.path.join(current_app.static_folder, settings.signature_image)
                if os.path.exists(signature_path):
                    sig_img = PILImage.open(signature_path)
                    sig_width, sig_height = sig_img.size
                    # Scale signature to fit
                    max_sig_width = 3 * inch
                    max_sig_height = 1 * inch
                    scale_factor = min(max_sig_width/sig_width, max_sig_height/sig_height)
                    sig_width *= scale_factor
                    sig_height *= scale_factor
                    c.drawImage(signature_path, (width - sig_width)/2, 2.6*inch, width=sig_width, height=sig_height)
                else:
                    current_app.logger.warning(f"Signature image not found at {signature_path}")
            except Exception as e:
                current_app.logger.error(f"Error adding signature to certificate: {str(e)}")
        
        # Add instructor name
        instructor_name = settings.instructor_name or "Course Instructor"
        c.setFont("Helvetica", 12)
        c.drawCentredString(width/2, 2.3*inch, instructor_name)
        
        # Add footer text if available
        if settings.footer_text:
            c.setFont("Helvetica", 10)
            c.drawCentredString(width/2, 1.5*inch, settings.footer_text)
        
        # Add certificate ID
        c.setFont("Helvetica", 8)
        c.drawCentredString(width/2, 0.6*inch, f"Certificate ID: {certificate.certificate_id}")
        
        # Save the PDF
        c.save()
        
        current_app.logger.info(f"Successfully created PDF certificate at {output_path}")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error creating certificate PDF: {str(e)}")
        # Try to save a very simple certificate as a fallback
        try:
            c = canvas.Canvas(output_path, pagesize=landscape(letter))
            width, height = landscape(letter)
            c.setFont("Helvetica-Bold", 30)
            c.drawCentredString(width/2, height/2+1*inch, "CERTIFICATE OF COMPLETION")
            c.setFont("Helvetica-Bold", 24)
            c.drawCentredString(width/2, height/2, f"{user.name}")
            c.setFont("Helvetica", 18)
            c.drawCentredString(width/2, height/2-1*inch, f"has completed {course.title}")
            c.setFont("Helvetica", 12)
            c.drawCentredString(width/2, height/2-2*inch, f"Certificate ID: {certificate.certificate_id}")
            c.save()
            current_app.logger.info(f"Created fallback simple certificate at {output_path}")
            return True
        except Exception as fallback_error:
            current_app.logger.error(f"Failed to create fallback certificate: {str(fallback_error)}")
            return False

def get_user_certificates(user_id):
    """
    Get all certificates for a user
    
    Args:
        user_id (int): The ID of the user
        
    Returns:
        list: A list of Certificate objects
    """
    certificates = Certificate.query.filter_by(user_id=user_id).all()
    
    # Load related course data for each certificate
    for cert in certificates:
        cert.course = Course.query.get(cert.course_id)
    
    return certificates

def generate_verification_hash(certificate_id, user_id):
    """
    Generate a verification hash for the certificate
    
    Args:
        certificate_id (str): The certificate ID
        user_id (int): The user's ID
        
    Returns:
        str: A hash that can be used to verify the certificate
    """
    verification_string = f"{certificate_id}:{user_id}:{current_app.config['SECRET_KEY']}"
    return hashlib.sha256(verification_string.encode()).hexdigest()

def verify_certificate(certificate_id):
    """
    Verify a certificate by its ID
    
    Args:
        certificate_id (str): The unique ID of the certificate
        
    Returns:
        Certificate: The certificate if found, None otherwise
    """
    return Certificate.query.filter_by(certificate_id=certificate_id).first()

def issue_certificate_on_course_completion(user_id, course_id):
    """
    Check if a certificate should be issued for a course completion,
    and issue it if appropriate.
    
    Args:
        user_id (int): The ID of the user
        course_id (int): The ID of the completed course
        
    Returns:
        Certificate or None: The newly created certificate or None if not issued
    """
    from app.models import Course, Certificate, UserCourse, CertificateSettings
    
    # Get the course and check if it has certificates enabled
    course = Course.query.get(course_id)
    if not course or not course.has_certificate:
        current_app.logger.info(f"Course {course_id} does not have certificates enabled")
        return None
    
    # Check if the user has already received a certificate for this course
    existing_certificate = Certificate.query.filter_by(
        user_id=user_id, 
        course_id=course_id
    ).first()
    
    if existing_certificate:
        current_app.logger.info(f"User {user_id} already has a certificate for course {course_id}")
        return existing_certificate
    
    # Check if the user has completed the course
    enrollment = UserCourse.query.filter_by(
        user_id=user_id,
        course_id=course_id
    ).first()
    
    if not enrollment or not enrollment.completed:
        current_app.logger.info(f"User {user_id} has not completed course {course_id}")
        return None
    
    # Get certificate settings
    settings = CertificateSettings.get_settings()
    
    # Check if auto-issue is enabled in the settings
    if not settings.auto_issue:
        current_app.logger.info("Auto-issue certificates is disabled in settings")
        return None
    
    # Everything checks out, generate the certificate
    certificate = generate_certificate(user_id, course_id)
    
    # If generation was successful and email notification is enabled, send email
    if certificate and settings.send_email:
        try:
            from app.utils.email import EmailService
            from app.models import User
            
            user = User.query.get(user_id)
            EmailService.send_certificate_email(user, course, certificate)
        except Exception as e:
            current_app.logger.error(f"Error sending certificate email: {str(e)}")
    
    return certificate

def generate_preview_certificate(template, sample_data):
    """
    Generate a preview certificate for a template
    
    Args:
        template (CertificateTemplate): The certificate template to use
        sample_data (dict): Sample data for the certificate preview
        
    Returns:
        bytes: The certificate PDF as bytes
    """
    from io import BytesIO
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    
    # Create a BytesIO object to store the PDF
    buffer = BytesIO()
    
    # Create the PDF canvas
    c = canvas.Canvas(buffer, pagesize=landscape(letter))
    width, height = landscape(letter)
    
    # Parse colors from hex to ReportLab color objects
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))
    
    # Set colors from template
    bg_color = colors.Color(*hex_to_rgb(template.background_color)) if template.background_color else colors.white
    border_color = colors.Color(*hex_to_rgb(template.border_color)) if template.border_color else colors.black
    text_color = colors.Color(*hex_to_rgb(template.text_color)) if template.text_color else colors.black
    
    # Set background color
    c.setFillColor(bg_color)
    c.rect(0, 0, width, height, fill=True)
    
    # Draw border
    c.setStrokeColor(border_color)
    c.setLineWidth(3)
    c.rect(0.5*inch, 0.5*inch, width-inch, height-inch)
    
    # Add watermark
    c.setFillColor(colors.Color(0.78, 0.78, 0.78, 0.3))  # Light gray with 30% opacity
    c.setFont("Helvetica", 80)
    c.saveState()
    c.translate(width/2, height/2)
    c.rotate(-30)
    c.drawCentredString(0, 0, "PREVIEW")
    c.restoreState()
    
    # Add platform logo/name at top
    platform_name = current_app.config.get('PLATFORM_NAME', 'Learning Platform')
    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height-1.5*inch, platform_name)
    
    # Add logo if available
    if template.logo_path:
        try:
            logo_path = os.path.join(current_app.static_folder, template.logo_path)
            if os.path.exists(logo_path):
                logo = PILImage.open(logo_path)
                logo_width, logo_height = logo.size
                # Scale logo to fit
                max_logo_width = 2 * inch
                max_logo_height = 1.5 * inch
                scale_factor = min(max_logo_width/logo_width, max_logo_height/logo_height)
                logo_width *= scale_factor
                logo_height *= scale_factor
                c.drawImage(logo_path, (width - logo_width)/2, height-2*inch, width=logo_width, height=logo_height)
        except Exception as e:
            current_app.logger.error(f"Error adding logo to certificate preview: {str(e)}")
    
    # Add certificate title
    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(width/2, height-2.5*inch, template.certificate_title)
    
    # Add user name
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(width/2, height/2, sample_data.get("student_name", "Student Name"))
    
    # Add certificate text
    c.setFont("Helvetica", 18)
    c.drawCentredString(width/2, height/2-0.5*inch, template.certificate_text)
    
    # Add course name
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height/2-1.1*inch, sample_data.get("course_title", "Course Title"))
    
    # Add issue date - replacing datetime.utcnow with get_utc_now
    issue_date = sample_data.get("completion_date", get_utc_now().strftime("%B %d, %Y"))
    c.setFont("Helvetica", 14)
    c.drawCentredString(width/2, height/2-1.6*inch, f"Issued on {issue_date}")
    
    # Add verification text
    verify_url = url_for('certificates.verify', certificate_id=sample_data.get("certificate_id", "SAMPLE-ID"), _external=True)
    c.setFont("Helvetica", 10)
    c.drawCentredString(width/2, 1.2*inch, f"To verify this certificate, please visit:")
    c.drawCentredString(width/2, 0.9*inch, verify_url)
    
    # Add signature
    c.line(width/2-1.5*inch, 2.5*inch, width/2+1.5*inch, 2.5*inch)
    
    # Add signature image if available
    if template.signature_path:
        try:
            signature_path = os.path.join(current_app.static_folder, template.signature_path)
            if os.path.exists(signature_path):
                sig_img = PILImage.open(signature_path)
                sig_width, sig_height = sig_img.size
                # Scale signature to fit
                max_sig_width = 3 * inch
                max_sig_height = 1 * inch
                scale_factor = min(max_sig_width/sig_width, max_sig_height/sig_height)
                sig_width *= scale_factor
                sig_height *= scale_factor
                c.drawImage(signature_path, (width - sig_width)/2, 2.6*inch, width=sig_width, height=sig_height)
        except Exception as e:
            current_app.logger.error(f"Error adding signature to certificate preview: {str(e)}")
    
    # Add instructor name
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, 2.3*inch, template.instructor_name)
    
    # Add footer text if available
    if template.footer_text:
        c.setFont("Helvetica", 10)
        c.drawCentredString(width/2, 1.5*inch, template.footer_text)
    
    # Add certificate ID
    c.setFont("Helvetica", 8)
    c.drawCentredString(width/2, 0.6*inch, f"Certificate ID: {sample_data.get('certificate_id', 'SAMPLE-ID')}")
    
    # Save the PDF
    c.save()
    
    # Get the PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes
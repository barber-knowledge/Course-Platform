import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from app.extensions import db
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Course, Quiz, QuizQuestion, QuizAnswer, Video, CoursePDF, User, PlatformConfig, EmailTemplate, CertificateSettings, Certificate, CertificateTemplate
from app.blueprints.admin import admin
from sqlalchemy import func

@admin.before_request
def check_admin():
    """Ensure only admin users can access admin routes"""
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('You do not have permission to access the admin area.', 'danger')
        return redirect(url_for('main.index'))

@admin.route('/')
@login_required
def index():
    """Admin dashboard home page"""
    courses_count = Course.query.count()
    quizzes_count = Quiz.query.count()
    videos_count = Video.query.count() 
    pdfs_count = CoursePDF.query.count()
    users_count = User.query.count()
    
    # Create a stats dictionary with all required values for the template
    from app.models import UserCourse, Payment
    enrollments_count = UserCourse.query.count()
    
    # Calculate revenue from payments if possible
    try:
        from sqlalchemy import func
        revenue = db.session.query(func.sum(Payment.amount)).scalar() or 0
    except Exception:
        # If Payment table doesn't exist or there's another issue
        revenue = 0
    
    stats = {
        'courses': courses_count,
        'users': users_count,
        'quizzes': quizzes_count, 
        'videos': videos_count,
        'pdfs': pdfs_count,
        'enrollments': enrollments_count,
        'revenue': revenue
    }
    
    # Get recent enrollments and users for dashboard tables
    try:
        recent_enrollments = UserCourse.query.order_by(UserCourse.enrollment_date.desc()).limit(5).all()
    except Exception:
        recent_enrollments = []
    
    try:
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    except Exception:
        recent_users = []
    
    return render_template('admin/index.html',
                          stats=stats,
                          recent_enrollments=recent_enrollments,
                          recent_users=recent_users)

# Email settings and templates routes
@admin.route('/settings', methods=['GET', 'POST'])
@login_required
def platform_settings():
    """Configure platform settings including name, colors, and payment options"""
    config = PlatformConfig.get_config()
    
    if request.method == 'POST':
        # Update basic platform settings
        config.platform_name = request.form.get('platform_name')
        config.primary_color = request.form.get('primary_color')
        config.secondary_color = request.form.get('secondary_color')
        config.welcome_message = request.form.get('welcome_message')
        
        # Handle logo upload
        if 'logo' in request.files and request.files['logo'].filename:
            logo_file = request.files['logo']
            if allowed_file(logo_file.filename, ['jpg', 'jpeg', 'png']):
                filename = secure_filename(f"{uuid.uuid4()}_{logo_file.filename}")
                upload_folder = os.path.join(current_app.static_folder, 'uploads', 'logos')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                logo_path = os.path.join(upload_folder, filename)
                logo_file.save(logo_path)
                # Store relative path for the logo
                config.logo_path = f"uploads/logos/{filename}"
        
        # Handle logo removal if requested
        if 'remove_logo' in request.form and request.form.get('remove_logo') == 'on':
            if config.logo_path and os.path.exists(os.path.join(current_app.static_folder, config.logo_path)):
                os.remove(os.path.join(current_app.static_folder, config.logo_path))
            config.logo_path = None
        
        # Update Stripe settings
        config.stripe_enabled = 'stripe_enabled' in request.form
        config.stripe_publishable_key = request.form.get('stripe_publishable_key')
        
        # Only update secret key if provided
        stripe_secret_key = request.form.get('stripe_secret_key')
        if stripe_secret_key:
            config.stripe_secret_key = stripe_secret_key
        
        db.session.commit()
        flash('Platform settings updated successfully!', 'success')
        return redirect(url_for('admin.platform_settings'))
    
    return render_template('admin/settings/index.html', config=config)

@admin.route('/email-settings', methods=['GET', 'POST'])
@login_required
def email_settings():
    """Configure SMTP settings for email sending"""
    config = PlatformConfig.get_config()
    
    if request.method == 'POST':
        # Update SMTP settings
        config.smtp_server = request.form.get('smtp_server')
        config.smtp_port = request.form.get('smtp_port', type=int)
        config.smtp_username = request.form.get('smtp_username')
        
        # Only update password if provided
        smtp_password = request.form.get('smtp_password')
        if smtp_password:
            config.smtp_password = smtp_password
            
        config.smtp_use_tls = 'smtp_use_tls' in request.form
        config.smtp_use_ssl = 'smtp_use_ssl' in request.form
        config.smtp_default_sender = request.form.get('smtp_default_sender')
        config.smtp_enabled = 'smtp_enabled' in request.form
        
        # Update RabbitMQ settings
        config.rabbitmq_host = request.form.get('rabbitmq_host')
        config.rabbitmq_port = request.form.get('rabbitmq_port', type=int)
        config.rabbitmq_username = request.form.get('rabbitmq_username')
        config.rabbitmq_vhost = request.form.get('rabbitmq_vhost')
        
        # Only update password if provided
        rabbitmq_password = request.form.get('rabbitmq_password')
        if rabbitmq_password:
            config.rabbitmq_password = rabbitmq_password
            
        config.rabbitmq_enabled = 'rabbitmq_enabled' in request.form
        
        db.session.commit()
        flash('Email settings updated successfully!', 'success')
        return redirect(url_for('admin.email_settings'))
    
    return render_template('admin/settings/email.html', config=config)

@admin.route('/email-templates')
@login_required
def email_templates():
    """List all email templates"""
    templates = EmailTemplate.query.all()
    
    # Initialize default templates if none exist
    if not templates:
        EmailTemplate.init_default_templates()
        templates = EmailTemplate.query.all()
    
    return render_template('admin/settings/email_templates.html', templates=templates, user=current_user)

@admin.route('/email-templates/<int:template_id>', methods=['GET', 'POST'])
@login_required
def edit_email_template(template_id):
    """Edit an email template"""
    template = EmailTemplate.query.get_or_404(template_id)
    
    if request.method == 'POST':
        template.name = request.form.get('name')
        template.subject = request.form.get('subject')
        template.body_html = request.form.get('body_html')
        template.body_text = request.form.get('body_text')
        template.description = request.form.get('description')
        template.is_active = 'is_active' in request.form
        
        db.session.commit()
        flash('Email template updated successfully!', 'success')
        return redirect(url_for('admin.email_templates'))
    
    return render_template('admin/settings/edit_email_template.html', template=template, user=current_user)

@admin.route('/email-templates/<int:template_id>/reset', methods=['POST'])
@login_required
def reset_email_template(template_id):
    """Reset an email template to its default value"""
    template = EmailTemplate.query.get_or_404(template_id)
    
    # Get the template key
    template_key = template.template_key
    
    # Delete the existing template
    db.session.delete(template)
    db.session.commit()
    
    # Reinitialize default templates
    EmailTemplate.init_default_templates()
    
    flash('Email template has been reset to default.', 'success')
    return redirect(url_for('admin.email_templates'))

@admin.route('/test-email', methods=['POST'])
@login_required
def test_email():
    """Send a test email to verify SMTP settings"""
    try:
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({'success': False, 'error': 'Email address is required'}), 400
            
        email = data['email']
        
        # Create a test email
        from app.utils.email import EmailService
        
        # Get the platform config
        config = PlatformConfig.get_config()
        
        # If SMTP is not configured or enabled, return an error
        if not config.smtp_enabled or not config.smtp_server:
            return jsonify({
                'success': False, 
                'error': 'Email sending is disabled or not configured. Please configure SMTP settings first.'
            }), 400
            
        # Create a simple test email
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1>Test Email from {config.platform_name}</h1>
            <p>This is a test email to verify that your SMTP settings are correctly configured.</p>
            <p>If you're receiving this email, it means your email configuration is working properly!</p>
            <p style="margin-top: 30px;">Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """
        
        text_body = f"""
        Test Email from {config.platform_name}
        
        This is a test email to verify that your SMTP settings are correctly configured.
        
        If you're receiving this email, it means your email configuration is working properly!
        
        Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        # Send the test email
        success = EmailService.send_email(
            subject=f"Test Email from {config.platform_name}",
            recipients=[email],
            html_body=html_body,
            text_body=text_body,
            sync=True  # Send synchronously to get immediate feedback
        )
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to send test email. Check your SMTP settings and server logs for details.'})
            
    except Exception as e:
        current_app.logger.error(f"Error sending test email: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Course Management Routes
@admin.route('/courses')
@login_required
def courses():
    """List all courses"""
    courses = Course.query.all()
    return render_template('admin/courses/index.html', courses=courses)

@admin.route('/courses/new', methods=['GET', 'POST'])
@login_required
def new_course():
    """Create a new course"""
    from app.models import CertificateTemplate
    
    # Get all certificate templates
    certificate_templates = CertificateTemplate.query.all()
    # Ensure there's at least a default template
    if not certificate_templates:
        default_template = CertificateTemplate.get_default_template()
        certificate_templates = [default_template]
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        price = float(request.form.get('price', 0))
        is_published = 'is_published' in request.form  # For content accessibility to enrolled students
        is_active = 'is_active' in request.form  # For toggling visibility in public listings
        has_certificate = 'has_certificate' in request.form  # For enabling course certificates
        certificate_template_id = request.form.get('certificate_template_id')
        
        # Convert certificate_template_id to int if it exists and has_certificate is True
        if has_certificate and certificate_template_id:
            certificate_template_id = int(certificate_template_id)
        else:
            certificate_template_id = None
            
        # Handle image upload
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and allowed_file(image_file.filename, ['jpg', 'jpeg', 'png']):
                filename = secure_filename(f"{uuid.uuid4()}_{image_file.filename}")
                upload_folder = os.path.join(current_app.static_folder, 'uploads', 'courses')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                image_path = os.path.join(upload_folder, filename)
                image_file.save(image_path)
                # Store path for image_url
                image_url = f"/static/uploads/courses/{filename}"
            else:
                image_url = None
        else:
            image_url = None
            
        course = Course(
            title=title,
            description=description,
            price=price,
            is_published=is_published,
            is_active=is_active,
            has_certificate=has_certificate,
            certificate_template_id=certificate_template_id,
            image_url=image_url
        )
        
        db.session.add(course)
        db.session.commit()
        
        flash('Course created successfully!', 'success')
        return redirect(url_for('admin.courses'))
        
    # Changed to use the form.html template
    return render_template('admin/courses/form.html', 
                          course=None, 
                          certificate_templates=certificate_templates)

@admin.route('/courses/<int:course_id>', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    """Edit an existing course"""
    from app.models import CertificateTemplate
    
    course = Course.query.get_or_404(course_id)
    
    # Get all certificate templates
    certificate_templates = CertificateTemplate.query.all()
    # Ensure there's at least a default template
    if not certificate_templates:
        default_template = CertificateTemplate.get_default_template()
        certificate_templates = [default_template]
    
    if request.method == 'POST':
        course.title = request.form.get('title')
        course.description = request.form.get('description')
        course.price = float(request.form.get('price', 0))
        course.is_published = 'is_published' in request.form  # For content accessibility to enrolled students
        course.is_active = 'is_active' in request.form  # For toggling visibility in public listings
        course.has_certificate = 'has_certificate' in request.form  # For enabling course certificates
        
        # Handle certificate template selection if certificates are enabled
        if course.has_certificate:
            certificate_template_id = request.form.get('certificate_template_id')
            if certificate_template_id:
                course.certificate_template_id = int(certificate_template_id)
            else:
                # Use default template if none selected
                default_template = CertificateTemplate.get_default_template()
                course.certificate_template_id = default_template.id
        else:
            course.certificate_template_id = None
        
        # Handle image upload
        if 'image' in request.files and request.files['image'].filename:
            image_file = request.files['image']
            if allowed_file(image_file.filename, ['jpg', 'jpeg', 'png']):
                filename = secure_filename(f"{uuid.uuid4()}_{image_file.filename}")
                upload_folder = os.path.join(current_app.static_folder, 'uploads', 'courses')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                image_path = os.path.join(upload_folder, filename)
                image_file.save(image_path)
                course.image_url = f"/static/uploads/courses/{filename}"  # Changed from image to image_url
        
        db.session.commit()
        flash('Course updated successfully!', 'success')
        return redirect(url_for('admin.courses'))
    
    # Changed to use the form.html template
    return render_template('admin/courses/form.html', course=course, certificate_templates=certificate_templates)

@admin.route('/courses/<int:course_id>/delete', methods=['POST'])
@login_required
def delete_course(course_id):
    """Delete a course"""
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    
    flash('Course deleted successfully!', 'success')
    return redirect(url_for('admin.courses'))

# Video Management Routes
VIDEO_UPLOAD_FOLDER = 'videos'
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg'}

def ensure_upload_folder(folder_name):
    """Creates the upload folder if it doesn't exist."""
    upload_path = os.path.join(current_app.static_folder, 'uploads', folder_name)
    if not os.path.exists(upload_path):
        try:
            os.makedirs(upload_path)
        except Exception as e:
            current_app.logger.error(f"Failed to create directory {upload_path}: {str(e)}")
            return None
    return upload_path

@admin.route('/courses/<int:course_id>/videos')
@login_required
def videos(course_id):
    """List videos for a course"""
    course = Course.query.get_or_404(course_id)
    videos = Video.query.filter_by(course_id=course_id).order_by(Video.sequence_order).all()
    return render_template('admin/videos/index.html', course=course, videos=videos)

@admin.route('/courses/<int:course_id>/videos/new', methods=['GET', 'POST'])
@login_required
def new_video(course_id):
    """Add a new video to a course"""
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        sequence_order = int(request.form.get('sequence_order', 1))
        duration_seconds = int(request.form.get('duration_seconds', 0)) # Use duration_seconds
        is_free = 'is_free' in request.form

        video_file = request.files.get('video_file')
        
        if not video_file or not video_file.filename:
            flash('Video file is required.', 'danger')
            return render_template('admin/videos/form.html', course=course, video=None)

        if not allowed_file(video_file.filename, ALLOWED_VIDEO_EXTENSIONS):
            flash('Invalid video file type. Allowed types: mp4, webm, ogg', 'danger')
            return render_template('admin/videos/form.html', course=course, video=None)

        upload_folder = ensure_upload_folder(VIDEO_UPLOAD_FOLDER)
        if not upload_folder:
             flash('Could not create upload directory.', 'danger')
             return render_template('admin/videos/form.html', course=course, video=None)

        try:
            filename = secure_filename(f"{uuid.uuid4()}_{video_file.filename}")
            video_save_path = os.path.join(upload_folder, filename)
            video_file.save(video_save_path)
            # Store relative path for URL generation
            video_path = os.path.join('uploads', VIDEO_UPLOAD_FOLDER, filename).replace('\\', '/') 
        except Exception as e:
            flash(f'Failed to save video file: {str(e)}', 'danger')
            current_app.logger.error(f"Video upload failed: {str(e)}")
            return render_template('admin/videos/form.html', course=course, video=None)

        # Create a new video
        video = Video(
            course_id=course_id,
            title=title,
            description=description,
            video_path=video_path, # Use video_path
            sequence_order=sequence_order,
            duration_seconds=duration_seconds, # Use duration_seconds
            is_free=is_free # Add is_free
        )
        
        db.session.add(video)
        db.session.commit()
        
        flash('Video added successfully!', 'success')
        return redirect(url_for('admin.videos', course_id=course_id))
        
    # GET request
    return render_template('admin/videos/form.html', course=course, video=None) # Pass video=None for new form

@admin.route('/videos/<int:video_id>', methods=['GET', 'POST'])
@login_required
def edit_video(video_id):
    """Edit a video"""
    video = Video.query.get_or_404(video_id)
    course = video.course # Get course from video relationship
    
    if request.method == 'POST':
        video.title = request.form.get('title')
        video.description = request.form.get('description')
        video.sequence_order = int(request.form.get('sequence_order', 1))
        video.duration_seconds = int(request.form.get('duration_seconds', 0)) # Use duration_seconds
        video.is_free = 'is_free' in request.form # Update is_free

        video_file = request.files.get('video_file')

        # Handle optional video replacement
        if video_file and video_file.filename:
            if not allowed_file(video_file.filename, ALLOWED_VIDEO_EXTENSIONS):
                flash('Invalid video file type. Allowed types: mp4, webm, ogg', 'danger')
                return render_template('admin/videos/form.html', course=course, video=video)

            upload_folder = ensure_upload_folder(VIDEO_UPLOAD_FOLDER)
            if not upload_folder:
                 flash('Could not access upload directory.', 'danger')
                 return render_template('admin/videos/form.html', course=course, video=video)

            try:
                # Optionally remove old file
                old_file_path = os.path.join(current_app.static_folder, video.video_path)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
                
                # Save new file
                filename = secure_filename(f"{uuid.uuid4()}_{video_file.filename}")
                video_save_path = os.path.join(upload_folder, filename)
                video_file.save(video_save_path)
                # Update relative path
                video.video_path = os.path.join('uploads', VIDEO_UPLOAD_FOLDER, filename).replace('\\', '/')
            except Exception as e:
                flash(f'Failed to replace video file: {str(e)}', 'danger')
                current_app.logger.error(f"Video replacement failed: {str(e)}")
                return render_template('admin/videos/form.html', course=course, video=video)

        db.session.commit()
        
        flash('Video updated successfully!', 'success')
        return redirect(url_for('admin.videos', course_id=video.course_id))
        
    # GET request
    return render_template('admin/videos/form.html', course=course, video=video) # Pass existing video object

@admin.route('/videos/<int:video_id>/delete', methods=['POST'])
@login_required
def delete_video(video_id):
    """Delete a video"""
    video = Video.query.get_or_404(video_id)
    course_id = video.course_id
    
    # Attempt to delete the video file from storage
    try:
        file_path = os.path.join(current_app.static_folder, video.video_path)
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        flash(f'Could not delete video file: {str(e)}', 'warning')
        current_app.logger.error(f"Failed to delete video file {video.video_path}: {str(e)}")

    db.session.delete(video)
    db.session.commit()
    
    flash('Video deleted successfully!', 'success')
    return redirect(url_for('admin.videos', course_id=course_id))

@admin.route('/courses/<int:course_id>/videos/reorder', methods=['POST'])
@login_required
def reorder_videos(course_id):
    """Update the sequence order of videos after drag and drop"""
    # Make sure course exists
    course = Course.query.get_or_404(course_id)
    
    # Get the reordered items from the request
    data = request.get_json()
    if not data or 'items' not in data:
        return jsonify({'success': False, 'error': 'Invalid data'}), 400
        
    try:
        # Update each video's sequence_order
        for item in data['items']:
            video_id = item.get('id')
            new_order = item.get('order')
            
            if video_id and new_order:
                video = Video.query.get(video_id)
                if video and video.course_id == course_id:
                    video.sequence_order = new_order
        
        # Commit all changes at once
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error reordering videos: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# PDF Management Routes
@admin.route('/courses/<int:course_id>/pdfs')
@login_required
def pdfs(course_id):
    """List PDFs for a course"""
    course = Course.query.get_or_404(course_id)
    pdfs = CoursePDF.query.filter_by(course_id=course_id).order_by(CoursePDF.sequence_order).all()
    return render_template('admin/pdfs/index.html', course=course, pdfs=pdfs)

@admin.route('/courses/<int:course_id>/pdfs/new', methods=['GET', 'POST'])
@login_required
def new_pdf(course_id):
    """Add a new PDF to a course"""
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        sequence_order = int(request.form.get('sequence_order', 1))
        
        # Handle PDF upload
        if 'pdf_file' in request.files:
            pdf_file = request.files['pdf_file']
            if pdf_file and allowed_file(pdf_file.filename, ['pdf']):
                filename = secure_filename(f"{uuid.uuid4()}_{pdf_file.filename}")
                pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'pdfs', filename)
                os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
                pdf_file.save(pdf_path)
                
                # Create the PDF record
                pdf = CoursePDF(
                    course_id=course_id,
                    title=title,
                    description=description,
                    pdf_path=f"/static/uploads/pdfs/{filename}",
                    sequence_order=sequence_order
                )
                
                db.session.add(pdf)
                db.session.commit()
                
                flash('PDF added successfully!', 'success')
                return redirect(url_for('admin.pdfs', course_id=course_id))
            else:
                flash('Invalid file. Please upload a PDF.', 'danger')
        else:
            flash('No file selected.', 'danger')
            
    return render_template('admin/pdfs/new.html', course=course)

@admin.route('/pdfs/<int:pdf_id>', methods=['GET', 'POST'])
@login_required
def edit_pdf(pdf_id):
    """Edit a PDF document"""
    pdf = CoursePDF.query.get_or_404(pdf_id)
    
    if request.method == 'POST':
        pdf.title = request.form.get('title')
        pdf.description = request.form.get('description')
        pdf.sequence_order = int(request.form.get('sequence_order', 1))
        
        # Handle PDF replacement
        if 'pdf_file' in request.files and request.files['pdf_file'].filename:
            pdf_file = request.files['pdf_file']
            if pdf_file and allowed_file(pdf_file.filename, ['pdf']):
                filename = secure_filename(f"{uuid.uuid4()}_{pdf_file.filename}")
                pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'pdfs', filename)
                os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
                pdf_file.save(pdf_path)
                
                # Update the PDF path
                pdf.pdf_path = f"/static/uploads/pdfs/{filename}"
        
        db.session.commit()
        flash('PDF updated successfully!', 'success')
        return redirect(url_for('admin.pdfs', course_id=pdf.course_id))
        
    return render_template('admin/pdfs/edit.html', pdf=pdf)

@admin.route('/pdfs/<int:pdf_id>/delete', methods=['POST'])
@login_required
def delete_pdf(pdf_id):
    """Delete a PDF document"""
    pdf = CoursePDF.query.get_or_404(pdf_id)
    course_id = pdf.course_id
    
    # TODO: Delete the actual file from the file system
    
    db.session.delete(pdf)
    db.session.commit()
    
    flash('PDF deleted successfully!', 'success')
    return redirect(url_for('admin.pdfs', course_id=course_id))

# Quiz Management Routes
@admin.route('/courses/<int:course_id>/quizzes')
@login_required
def quizzes(course_id):
    """List quizzes for a course"""
    course = Course.query.get_or_404(course_id)
    quizzes = Quiz.query.filter_by(course_id=course_id).all()
    return render_template('admin/quizzes/index.html', course=course, quizzes=quizzes)

@admin.route('/courses/<int:course_id>/quizzes/new', methods=['GET', 'POST'])
@login_required
def new_quiz(course_id):
    """Create a new quiz for a course"""
    course = Course.query.get_or_404(course_id)
    
    # Check if course already has a quiz
    existing_quiz = Quiz.query.filter_by(course_id=course_id).first()
    if existing_quiz:
        flash('This course already has a quiz. You can only have one quiz per course.', 'warning')
        return redirect(url_for('admin.quizzes', course_id=course_id))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        passing_percentage = int(request.form.get('pass_percentage', 70))
        
        # Create the quiz
        quiz = Quiz(
            course_id=course_id,
            title=title,
            description=description,
            passing_percentage=passing_percentage
        )
        
        db.session.add(quiz)
        db.session.commit()
        
        flash('Quiz created successfully! Now add questions to your quiz.', 'success')
        return redirect(url_for('admin.edit_quiz', quiz_id=quiz.id))
    
    return render_template('admin/quizzes/new.html', course=course)

@admin.route('/quizzes/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def edit_quiz(quiz_id):
    """Edit a quiz and manage its questions"""
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).all()
    
    if request.method == 'POST':
        quiz.title = request.form.get('title')
        quiz.description = request.form.get('description')
        quiz.passing_percentage = int(request.form.get('pass_percentage', 70))
        
        db.session.commit()
        flash('Quiz updated successfully!', 'success')
        return redirect(url_for('admin.edit_quiz', quiz_id=quiz_id))
    
    return render_template('admin/quizzes/edit.html', quiz=quiz, questions=questions)

@admin.route('/quizzes/<int:quiz_id>/delete', methods=['POST'])
@login_required
def delete_quiz(quiz_id):
    """Delete a quiz"""
    quiz = Quiz.query.get_or_404(quiz_id)
    course_id = quiz.course_id
    
    db.session.delete(quiz)
    db.session.commit()
    
    flash('Quiz deleted successfully!', 'success')
    return redirect(url_for('admin.quizzes', course_id=course_id))

@admin.route('/quizzes/<int:quiz_id>/questions/new', methods=['GET', 'POST'])
@login_required
def new_question(quiz_id):
    """Add a new question to a quiz"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if request.method == 'POST':
        question_text = request.form.get('question_text')
        question_type = 'single_choice'  # Force single choice type
        points = int(request.form.get('points', 1))
        
        # Get the max sequence_order or default to 0
        max_sequence = db.session.query(func.max(QuizQuestion.sequence_order))\
                        .filter(QuizQuestion.quiz_id == quiz_id).scalar() or 0
        sequence_order = max_sequence + 1
        
        # Create the question
        question = QuizQuestion(
            quiz_id=quiz_id,
            question_text=question_text,
            question_type=question_type,
            points=points,
            sequence_order=sequence_order
        )
        
        db.session.add(question)
        db.session.commit()
        
        # Process exactly 4 answers
        answers = request.form.getlist('answer_text[]')
        correct_answer_index = request.form.get('is_correct')
        
        if len(answers) != 4:
            flash('Exactly 4 answers are required.', 'danger')
            db.session.delete(question)
            db.session.commit()
            return redirect(url_for('admin.new_question', quiz_id=quiz_id))
            
        if correct_answer_index is None:
            flash('You must select a correct answer.', 'danger')
            db.session.delete(question)
            db.session.commit()
            return redirect(url_for('admin.new_question', quiz_id=quiz_id))
        
        # Convert to integer
        correct_answer_index = int(correct_answer_index)
        
        # Add all 4 answers, marking the correct one
        for i, answer_text in enumerate(answers):
            if answer_text.strip():
                is_correct = (i == correct_answer_index)
                answer = QuizAnswer(
                    question_id=question.id,
                    answer_text=answer_text,
                    is_correct=is_correct
                )
                db.session.add(answer)
        
        db.session.commit()
        flash('Question added successfully!', 'success')
        return redirect(url_for('admin.edit_quiz', quiz_id=quiz_id))
    
    return render_template('admin/questions/new.html', quiz=quiz)

@admin.route('/questions/<int:question_id>', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    """Edit a quiz question and its answers"""
    question = QuizQuestion.query.get_or_404(question_id)
    
    if request.method == 'POST':
        question.question_text = request.form.get('question_text')
        question.points = int(request.form.get('points', 1))
        
        # Process exactly 4 answers
        answers = request.form.getlist('answer_text[]')
        correct_answer_index = request.form.get('is_correct')
        
        if len(answers) != 4:
            flash('Exactly 4 answers are required.', 'danger')
            answers = QuizAnswer.query.filter_by(question_id=question_id).all()
            return render_template('admin/questions/edit.html', question=question, answers=answers)
            
        if correct_answer_index is None:
            flash('You must select a correct answer.', 'danger')
            answers = QuizAnswer.query.filter_by(question_id=question_id).all()
            return render_template('admin/questions/edit.html', question=question, answers=answers)
        
        # Convert to integer
        correct_answer_index = int(correct_answer_index)
        
        # Delete existing answers
        QuizAnswer.query.filter_by(question_id=question_id).delete()
        
        # Add all 4 answers, marking the correct one
        for i, answer_text in enumerate(answers):
            if answer_text.strip():
                is_correct = (i == correct_answer_index)
                answer = QuizAnswer(
                    question_id=question.id,
                    answer_text=answer_text,
                    is_correct=is_correct
                )
                db.session.add(answer)
        
        db.session.commit()
        flash('Question updated successfully!', 'success')
        return redirect(url_for('admin.edit_quiz', quiz_id=question.quiz_id))
    
    answers = QuizAnswer.query.filter_by(question_id=question_id).all()
    return render_template('admin/questions/edit.html', question=question, answers=answers)

@admin.route('/questions/<int:question_id>/delete', methods=['POST'])
@login_required
def delete_question(question_id):
    """Delete a question"""
    question = QuizQuestion.query.get_or_404(question_id)
    quiz_id = question.quiz_id
    
    db.session.delete(question)
    db.session.commit()
    
    flash('Question deleted successfully!', 'success')
    return redirect(url_for('admin.edit_quiz', quiz_id=quiz_id))

# User Management Routes
@admin.route('/users')
@login_required
def users():
    """List all users"""
    users = User.query.all()
    return render_template('admin/users/index.html', users=users)

@admin.route('/users/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Edit a user"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.name = request.form.get('name')
        user.email = request.form.get('email')
        user.is_admin = 'is_admin' in request.form
        
        # Only update password if provided
        password = request.form.get('password')
        if password and password.strip():
            user.set_password(password)
        
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.users'))
        
    return render_template('admin/users/edit.html', user=user)

@admin.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete a user"""
    user = User.query.get_or_404(user_id)
    
    if user.is_admin and User.query.filter_by(is_admin=True).count() <= 1:
        flash('Cannot delete the only admin user!', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
        
    return redirect(url_for('admin.users'))

# Enrollment Management Routes
@admin.route('/enrollments')
@login_required
def enrollments():
    """List all course enrollments"""
    from app.models import UserCourse
    
    enrollments = UserCourse.query.all()
    return render_template('admin/enrollments/index.html', enrollments=enrollments)

# Revenue Management Route
@admin.route('/revenue')
@login_required
def revenue():
    """View platform revenue statistics"""
    from app.models import Payment
    from sqlalchemy import func
    
    # Calculate revenue stats
    try:
        # Total revenue
        total_revenue = db.session.query(func.sum(Payment.amount)).scalar() or 0
        
        # Revenue by course
        course_revenue = db.session.query(
            Course.title,
            func.sum(Payment.amount).label('revenue')
        ).join(Payment, Payment.course_id == Course.id)\
         .group_by(Course.id)\
         .order_by(func.sum(Payment.amount).desc())\
         .all()
        
        # Recent payments 
        recent_payments = Payment.query.order_by(Payment.payment_date.desc()).limit(10).all()
        
    except Exception as e:
        current_app.logger.error(f"Error calculating revenue: {str(e)}")
        total_revenue = 0
        course_revenue = []
        recent_payments = []
    
    return render_template('admin/revenue/index.html', 
                          total_revenue=total_revenue,
                          course_revenue=course_revenue,
                          recent_payments=recent_payments)

# Certificate Management Routes
@admin.route('/certificate-settings', methods=['GET', 'POST'])
@login_required
def certificate_settings():
    """Configure certificate appearance and default settings"""
    config = PlatformConfig.get_config()
    
    if request.method == 'POST':
        # Update certificate settings
        config.certificate_title = request.form.get('certificate_title') or 'CERTIFICATE OF COMPLETION'
        config.certificate_primary_color = request.form.get('certificate_primary_color') or '#294767'
        config.certificate_text_color = request.form.get('certificate_text_color') or '#000000'
        config.certificate_border_color = request.form.get('certificate_border_color') or '#294767'
        config.auto_issue_certificates = 'auto_issue_certificates' in request.form
        config.certificate_email_notification = 'certificate_email_notification' in request.form
        
        # Handle signature image upload
        if 'signature_image' in request.files and request.files['signature_image'].filename:
            signature_file = request.files['signature_image']
            if allowed_file(signature_file.filename, ['jpg', 'jpeg', 'png']):
                filename = secure_filename(f"signature_{uuid.uuid4()}_{signature_file.filename}")
                upload_folder = os.path.join(current_app.static_folder, 'uploads', 'certificates')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                signature_path = os.path.join(upload_folder, filename)
                signature_file.save(signature_path)
                # Store relative path for the signature
                config.certificate_signature_path = f"uploads/certificates/{filename}"
        
        # Remove signature if requested
        if 'remove_signature' in request.form and request.form.get('remove_signature') == 'on':
            if config.certificate_signature_path and os.path.exists(os.path.join(current_app.static_folder, config.certificate_signature_path)):
                os.remove(os.path.join(current_app.static_folder, config.certificate_signature_path))
            config.certificate_signature_path = None
            
        # Save instructor name
        config.certificate_instructor_name = request.form.get('instructor_name') or ''
        
        db.session.commit()
        flash('Certificate settings updated successfully!', 'success')
        return redirect(url_for('admin.certificate_settings'))
    
    return render_template('admin/settings/certificates.html', config=config)

@admin.route('/certificates/settings', methods=['GET', 'POST'])
@login_required
def certificate_settings_v2():
    """Certificate settings configuration page"""
    from app.models import CertificateSettings
    from flask import flash, request, redirect, url_for
    from app.blueprints.admin.forms import CertificateSettingsForm
    
    settings = CertificateSettings.get_settings()
    form = CertificateSettingsForm()
    
    # Pre-populate form with existing settings
    if request.method == 'GET':
        form.certificate_title.data = settings.certificate_title or 'CERTIFICATE OF COMPLETION'
        form.certificate_text.data = settings.certificate_text
        form.footer_text.data = settings.footer_text
        form.instructor_name.data = settings.instructor_name
        form.certificate_border_color.data = settings.border_color
        form.certificate_text_color.data = settings.text_color
        form.background_color.data = settings.background_color
        form.certificate_font.data = settings.font
        form.auto_issue_certificates.data = settings.auto_issue
        form.send_certificate_email.data = settings.send_email
    
    if form.validate_on_submit():
        # Update settings from form
        settings.certificate_title = form.certificate_title.data
        settings.certificate_text = form.certificate_text.data
        settings.footer_text = form.footer_text.data
        settings.instructor_name = form.instructor_name.data
        settings.border_color = form.certificate_border_color.data
        settings.text_color = form.certificate_text_color.data
        settings.background_color = form.background_color.data
        settings.font = form.certificate_font.data
        settings.auto_issue = form.auto_issue_certificates.data
        settings.send_email = form.send_certificate_email.data
        
        # Handle logo upload
        if form.certificate_logo.data:
            logo_filename = secure_filename(f"cert_logo_{uuid.uuid4()}.png")
            upload_folder = os.path.join(current_app.static_folder, 'uploads', 'certificates')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            form.certificate_logo.data.save(os.path.join(upload_folder, logo_filename))
            settings.logo_path = f"uploads/certificates/{logo_filename}"
            
        # Handle signature upload
        if form.certificate_signature.data:
            signature_filename = secure_filename(f"cert_sign_{uuid.uuid4()}.png")
            upload_folder = os.path.join(current_app.static_folder, 'uploads', 'certificates')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            form.certificate_signature.data.save(os.path.join(upload_folder, signature_filename))
            settings.signature_path = f"uploads/certificates/{signature_filename}"
        
        db.session.commit()
        flash('Certificate settings updated successfully!', 'success')
        return redirect(url_for('admin.certificate_settings_v2'))
    
    return render_template('admin/certificates/settings.html', settings=settings, form=form)

@admin.route('/certificates')
@login_required
def certificates():
    """List all certificates issued on the platform"""
    certificates = Certificate.query.order_by(Certificate.created_at.desc()).all()
    
    # Load related course and user data
    for cert in certificates:
        cert.course = Course.query.get(cert.course_id)
        cert.user = User.query.get(cert.user_id)
        
    return render_template('admin/certificates/index.html', 
                          certificates=certificates,
                          title='All Certificates')

@admin.route('/certificates/preview')
@login_required
def certificate_preview():
    """Generate a certificate preview for the admin panel"""
    from app.models import CertificateSettings
    from app.utils.certificate import generate_certificate
    from flask import send_file
    import io
    
    settings = CertificateSettings.get_settings()
    
    # Generate a sample certificate
    sample_data = {
        "student_name": "John Doe",
        "course_title": "Sample Course Title",
        "completion_date": datetime.now().strftime("%B %d, %Y"),
        "course_id": "SAMPLE-COURSE",
        "certificate_id": "PREVIEW-CERT"
    }
    
    # Generate certificate as bytes
    certificate_bytes = generate_certificate(sample_data, settings)
    
    # Create a file-like object
    file_obj = io.BytesIO(certificate_bytes)
    file_obj.seek(0)
    
    # Send the file with the appropriate content type
    return send_file(file_obj, mimetype='application/pdf', as_attachment=False, download_name='certificate_preview.pdf')

# Certificate Template Management Routes
@admin.route('/certificate-templates')
@login_required
def certificate_templates():
    """List all certificate templates"""
    from app.models import CertificateTemplate
    
    templates = CertificateTemplate.query.all()
    
    # Ensure there's at least a default template
    if not templates:
        default_template = CertificateTemplate.get_default_template()
        templates = [default_template]
    
    return render_template('admin/certificates/templates/index.html', 
                          templates=templates,
                          title='Certificate Templates')

@admin.route('/certificate-templates/new', methods=['GET', 'POST'])
@login_required
def new_certificate_template():
    """Create a new certificate template"""
    from app.models import CertificateTemplate
    from app.blueprints.admin.forms import CertificateTemplateForm
    
    form = CertificateTemplateForm()
    
    if form.validate_on_submit():
        template = CertificateTemplate(
            name=form.name.data,
            description=form.description.data,
            certificate_title=form.certificate_title.data,
            certificate_text=form.certificate_text.data,
            footer_text=form.footer_text.data,
            instructor_name=form.instructor_name.data,
            border_color=form.border_color.data,
            text_color=form.text_color.data,
            background_color=form.background_color.data,
            font=form.font.data,
            is_default=form.is_default.data
        )
        
        # Handle logo upload
        if form.logo.data:
            logo_filename = secure_filename(f"cert_logo_{uuid.uuid4()}.png")
            upload_folder = os.path.join(current_app.static_folder, 'uploads', 'certificates')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            form.logo.data.save(os.path.join(upload_folder, logo_filename))
            template.logo_path = f"uploads/certificates/{logo_filename}"
            
        # Handle signature upload
        if form.signature.data:
            signature_filename = secure_filename(f"cert_sign_{uuid.uuid4()}.png")
            upload_folder = os.path.join(current_app.static_folder, 'uploads', 'certificates')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            form.signature.data.save(os.path.join(upload_folder, signature_filename))
            template.signature_path = f"uploads/certificates/{signature_filename}"
            
        # If this is set as default, remove default flag from other templates
        if template.is_default:
            CertificateTemplate.query.filter_by(is_default=True).update({'is_default': False})
            
        db.session.add(template)
        db.session.commit()
        
        flash('Certificate template created successfully!', 'success')
        return redirect(url_for('admin.certificate_templates'))
        
    return render_template('admin/certificates/templates/form.html', 
                          form=form,
                          title='New Certificate Template',
                          template=None)

@admin.route('/certificate-templates/<int:template_id>', methods=['GET', 'POST'])
@login_required
def edit_certificate_template(template_id):
    """Edit a certificate template"""
    from app.models import CertificateTemplate
    from app.blueprints.admin.forms import CertificateTemplateForm
    
    template = CertificateTemplate.query.get_or_404(template_id)
    form = CertificateTemplateForm(obj=template)
    
    if form.validate_on_submit():
        template.name = form.name.data
        template.description = form.description.data
        template.certificate_title = form.certificate_title.data
        template.certificate_text = form.certificate_text.data
        template.footer_text = form.footer_text.data
        template.instructor_name = form.instructor_name.data
        template.border_color = form.border_color.data
        template.text_color = form.text_color.data
        template.background_color = form.background_color.data
        template.font = form.font.data
        
        # If this is set as default, remove default flag from other templates
        if form.is_default.data and not template.is_default:
            CertificateTemplate.query.filter_by(is_default=True).update({'is_default': False})
        template.is_default = form.is_default.data
            
        # Handle logo upload
        if form.logo.data:
            logo_filename = secure_filename(f"cert_logo_{uuid.uuid4()}.png")
            upload_folder = os.path.join(current_app.static_folder, 'uploads', 'certificates')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            form.logo.data.save(os.path.join(upload_folder, logo_filename))
            
            # Delete old logo if exists
            if template.logo_path:
                old_logo_path = os.path.join(current_app.static_folder, template.logo_path)
                if os.path.exists(old_logo_path):
                    os.remove(old_logo_path)
                    
            template.logo_path = f"uploads/certificates/{logo_filename}"
            
        # Handle signature upload
        if form.signature.data:
            signature_filename = secure_filename(f"cert_sign_{uuid.uuid4()}.png")
            upload_folder = os.path.join(current_app.static_folder, 'uploads', 'certificates')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            form.signature.data.save(os.path.join(upload_folder, signature_filename))
            
            # Delete old signature if exists
            if template.signature_path:
                old_signature_path = os.path.join(current_app.static_folder, template.signature_path)
                if os.path.exists(old_signature_path):
                    os.remove(old_signature_path)
                    
            template.signature_path = f"uploads/certificates/{signature_filename}"
            
        db.session.commit()
        flash('Certificate template updated successfully!', 'success')
        return redirect(url_for('admin.certificate_templates'))
    
    # Pre-populate form with existing template values
    form.name.data = template.name
    form.description.data = template.description
    form.certificate_title.data = template.certificate_title
    form.certificate_text.data = template.certificate_text
    form.footer_text.data = template.footer_text
    form.instructor_name.data = template.instructor_name
    form.border_color.data = template.border_color
    form.text_color.data = template.text_color
    form.background_color.data = template.background_color
    form.font.data = template.font
    form.is_default.data = template.is_default
        
    return render_template('admin/certificates/templates/form.html', 
                          form=form,
                          title='Edit Certificate Template',
                          template=template)

@admin.route('/certificate-templates/<int:template_id>/delete', methods=['POST'])
@login_required
def delete_certificate_template(template_id):
    """Delete a certificate template"""
    from app.models import CertificateTemplate
    
    template = CertificateTemplate.query.get_or_404(template_id)
    
    # Don't allow deletion of the default template
    if template.is_default:
        flash('Cannot delete the default certificate template.', 'danger')
        return redirect(url_for('admin.certificate_templates'))
    
    # Make sure there's at least one template left after deletion
    if CertificateTemplate.query.count() <= 1:
        flash('Cannot delete the only certificate template. Create another one first.', 'danger')
        return redirect(url_for('admin.certificate_templates'))
    
    # Delete associated files
    if template.logo_path:
        logo_path = os.path.join(current_app.static_folder, template.logo_path)
        if os.path.exists(logo_path):
            os.remove(logo_path)
            
    if template.signature_path:
        signature_path = os.path.join(current_app.static_folder, template.signature_path)
        if os.path.exists(signature_path):
            os.remove(signature_path)
    
    # For courses using this template, reset to default template
    default_template = CertificateTemplate.get_default_template()
    for course in template.courses:
        course.certificate_template_id = default_template.id
    
    db.session.delete(template)
    db.session.commit()
    
    flash('Certificate template deleted successfully!', 'success')
    return redirect(url_for('admin.certificate_templates'))

@admin.route('/certificate-templates/<int:template_id>/preview')
@login_required
def preview_certificate_template(template_id):
    """Preview a certificate template"""
    from app.models import CertificateTemplate
    from flask import send_file
    import io
    
    template = CertificateTemplate.query.get_or_404(template_id)
    
    # Generate sample certificate using this template
    sample_data = {
        "student_name": "John Doe",
        "course_title": "Sample Course Title",
        "completion_date": datetime.now().strftime("%B %d, %Y"),
        "certificate_id": "PREVIEW-CERT-" + str(template_id)
    }
    
    # Generate certificate as bytes using a function that should be created in certificate.py
    from app.utils.certificate import generate_preview_certificate
    certificate_bytes = generate_preview_certificate(template, sample_data)
    
    # Create a file-like object
    file_obj = io.BytesIO(certificate_bytes)
    file_obj.seek(0)
    
    # Send the file with the appropriate content type
    return send_file(file_obj, mimetype='application/pdf', as_attachment=False, 
                     download_name=f'certificate_preview_{template.name}.pdf')
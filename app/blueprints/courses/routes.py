"""
Courses blueprint routes
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, send_from_directory, jsonify, current_app
from flask_login import login_required, current_user
from app.models import Course, UserCourse, Video, VideoProgress, CoursePDF, Quiz, QuizAttempt, Certificate
from app.utils.email import EmailService
from app import db
from datetime import datetime
import os
import json

bp = Blueprint('courses', __name__, url_prefix='/courses')

# Public-facing routes
@bp.route('/', methods=['GET'])
def index():
    """Public courses page"""
    courses = Course.query.filter_by(is_active=True).all()
    return render_template('courses/index.html', courses=courses)

@bp.route('/landing/<slug>', methods=['GET'])
def landing_page(slug):
    """Course landing/marketing page"""
    course = Course.query.filter_by(slug=slug).first_or_404()
    
    # Parse JSON fields for the landing page
    benefits = []
    if course.benefits:
        try:
            benefits = json.loads(course.benefits)
        except:
            pass
            
    faq = []
    if course.faq:
        try:
            faq = json.loads(course.faq)
        except:
            pass
            
    return render_template('courses/landing/index.html', 
                          course=course, 
                          benefits=benefits,
                          faq=faq,
                          meta_title=course.meta_title,
                          meta_description=course.meta_description)

@bp.route('/<int:course_id>')
def view(course_id):
    """
    View a specific course
    """
    # Get the course or return 404 if not found
    course = Course.query.get_or_404(course_id)
    
    # Check if course is active
    if not course.is_active and not (current_user.is_authenticated and current_user.is_admin):
        flash('This course is currently not available.', 'warning')
        return redirect(url_for('courses.index'))
    
    # Get course videos
    videos = Video.query.filter_by(course_id=course_id).order_by(Video.sequence_order).all()
    
    # Get course PDFs
    pdfs = CoursePDF.query.filter_by(course_id=course_id).all()
    
    # Check if user is enrolled
    is_enrolled = False
    if current_user.is_authenticated:
        enrollment = UserCourse.query.filter_by(
            user_id=current_user.id,
            course_id=course_id
        ).first()
        is_enrolled = enrollment is not None
    
    # Get quiz if exists
    quiz = Quiz.query.filter_by(course_id=course_id).first()
    
    return render_template('courses/view.html',
                          title=course.title,
                          course=course,
                          videos=videos,
                          pdfs=pdfs,
                          is_enrolled=is_enrolled,
                          quiz=quiz)

@bp.route('/<int:course_id>/enroll', methods=['GET', 'POST'])
@login_required
def enroll(course_id):
    """
    Enroll in a course
    """
    course = Course.query.get_or_404(course_id)
    
    # Check if already enrolled
    existing_enrollment = UserCourse.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if existing_enrollment:
        flash('You are already enrolled in this course.', 'info')
    else:
        # Check if the course requires payment
        if course.price > 0:
            # For now, just redirect to payment (to be implemented)
            flash('This course requires payment. Payment functionality coming soon!', 'warning')
            return redirect(url_for('courses.view', course_id=course_id))
        
        # Create enrollment record
        enrollment = UserCourse(
            user_id=current_user.id,
            course_id=course_id,
            enrollment_date=datetime.utcnow(),
            completed=False
        )
        
        db.session.add(enrollment)
        db.session.commit()
        
        # Send course enrollment confirmation email
        email_sent = EmailService.send_course_enrollment_email(current_user, course)
        if email_sent:
            current_app.logger.info(f"Course enrollment email sent to: {current_user.email} for course: {course.title}")
        else:
            current_app.logger.warning(f"Failed to send course enrollment email to: {current_user.email} for course: {course.title}")
        
        flash('You have successfully enrolled in this course!', 'success')
    
    return redirect(url_for('courses.view', course_id=course_id))

@bp.route('/enrolled')
@login_required
def enrolled():
    """
    View user's enrolled courses
    """
    # Get all courses the user is enrolled in
    user_courses = UserCourse.query.filter_by(user_id=current_user.id).all()
    
    # Get the actual course objects
    enrolled_courses = []
    for user_course in user_courses:
        course = Course.query.get(user_course.course_id)
        if course:
            # Add enrollment date and completion status to the course object
            course.enrollment_date = user_course.enrollment_date
            course.completed = user_course.completed
            enrolled_courses.append(course)
    
    return render_template('courses/enrolled.html', 
                          title='My Enrolled Courses',
                          courses=enrolled_courses)

@bp.route('/<int:course_id>/video/<int:video_id>')
@login_required
def video(course_id, video_id):
    """
    Watch a specific video in a course
    """
    # Get the course and video or return 404
    course = Course.query.get_or_404(course_id)
    current_video = Video.query.get_or_404(video_id)
    
    # Check if video belongs to the course
    if current_video.course_id != course_id:
        flash('This video does not belong to the selected course.', 'danger')
        return redirect(url_for('courses.view', course_id=course_id))
    
    # Check if the user is enrolled
    enrollment = UserCourse.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if not enrollment and not current_user.is_admin:
        flash('You need to enroll in this course to access its content.', 'warning')
        return redirect(url_for('courses.view', course_id=course_id))
    
    # Get all videos for the course for navigation
    course_videos = Video.query.filter_by(course_id=course_id).order_by(Video.sequence_order).all()
    
    # Get all PDFs for the course
    course_pdfs = CoursePDF.query.filter_by(course_id=course_id).order_by(CoursePDF.sequence_order).all()
    
    # Get or create video progress record
    video_progress = VideoProgress.query.filter_by(
        user_id=current_user.id,
        video_id=video_id
    ).first()
    
    if not video_progress:
        video_progress = VideoProgress(
            user_id=current_user.id,
            video_id=video_id,
            seconds_watched=0,
            is_completed=False,
            last_watched_at=datetime.utcnow()
        )
        db.session.add(video_progress)
        db.session.commit()
    
    # Calculate overall course progress
    all_videos = Video.query.filter_by(course_id=course_id).all()
    completed_videos = VideoProgress.query.filter_by(
        user_id=current_user.id,
        is_completed=True
    ).join(Video).filter(Video.course_id == course_id).count()
    
    if len(all_videos) > 0:
        progress_percent = (completed_videos / len(all_videos)) * 100
    else:
        progress_percent = 0
        
    # Check if quiz exists and is passed
    quiz = Quiz.query.filter_by(course_id=course_id).first()
    quiz_passed = False
    
    if quiz:
        quiz_attempt = QuizAttempt.query.filter_by(
            user_id=current_user.id,
            quiz_id=quiz.id,
            passed=True
        ).first()
        quiz_passed = quiz_attempt is not None
    
    # Get all progress records for the course videos
    all_progress = VideoProgress.query.filter_by(user_id=current_user.id).all()
    video_progress_dict = {vp.video_id: vp for vp in all_progress}
    
    # Check if all videos are completed
    videos_completed = completed_videos == len(all_videos)
    
    # Find next and previous videos
    next_video = None
    prev_video = None
    for i, vid in enumerate(course_videos):
        if vid.id == current_video.id:
            if i > 0:
                prev_video = course_videos[i - 1]
            if i < len(course_videos) - 1:
                next_video = course_videos[i + 1]
            break
    
    return render_template('courses/video.html',
                          title=f"{course.title} - {current_video.title}",
                          course=course,
                          current_video=current_video,
                          videos=course_videos,
                          pdfs=course_pdfs,
                          enrolled=True,
                          quiz=quiz,
                          quiz_passed=quiz_passed,
                          video_progress=video_progress_dict,
                          progress_percent=progress_percent,
                          videos_completed=videos_completed,
                          next_video=next_video,
                          prev_video=prev_video)

@bp.route('/<int:course_id>/pdf/<int:pdf_id>')
@login_required
def view_pdf(course_id, pdf_id):
    """
    View a specific PDF in a course
    """
    # Get the course and PDF or return 404
    course = Course.query.get_or_404(course_id)
    pdf = CoursePDF.query.get_or_404(pdf_id)
    
    # Check if PDF belongs to the course
    if pdf.course_id != course_id:
        flash('This PDF does not belong to the selected course.', 'danger')
        return redirect(url_for('courses.view', course_id=course_id))
    
    # Check if the user is enrolled
    enrollment = UserCourse.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if not enrollment and not current_user.is_admin:
        flash('You need to enroll in this course to access its content.', 'warning')
        return redirect(url_for('courses.view', course_id=course_id))
    
    # Get all videos for the course
    course_videos = Video.query.filter_by(course_id=course_id).order_by(Video.sequence_order).all()
    
    # Get all PDFs for the course
    course_pdfs = CoursePDF.query.filter_by(course_id=course_id).order_by(CoursePDF.sequence_order).all()
    
    # Calculate overall course progress
    all_videos = Video.query.filter_by(course_id=course_id).all()
    completed_videos = VideoProgress.query.filter_by(
        user_id=current_user.id,
        is_completed=True
    ).join(Video).filter(Video.course_id == course_id).count()
    
    if len(all_videos) > 0:
        progress_percent = (completed_videos / len(all_videos)) * 100
    else:
        progress_percent = 0
        
    # Get all progress records for the course videos
    all_progress = VideoProgress.query.filter_by(user_id=current_user.id).all()
    video_progress_dict = {vp.video_id: vp for vp in all_progress}
    
    return render_template('courses/pdf.html',
                          title=f"{course.title} - {pdf.title}",
                          course=course,
                          pdf=pdf,
                          videos=course_videos,
                          pdfs=course_pdfs,
                          enrolled=True,
                          video_progress=video_progress_dict,
                          progress_percent=progress_percent)

@bp.route('/<int:course_id>/pdf/<int:pdf_id>/complete', methods=['POST'])
@login_required
def complete_pdf(course_id, pdf_id):
    """
    Mark a PDF as read/completed via AJAX call
    """
    # Get the course and PDF
    course = Course.query.get_or_404(course_id)
    pdf = CoursePDF.query.get_or_404(pdf_id)
    
    # Check if PDF belongs to the course
    if pdf.course_id != course_id:
        return {'error': 'This PDF does not belong to the selected course.'}, 400
    
    # Check if the user is enrolled
    enrollment = UserCourse.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if not enrollment and not current_user.is_admin:
        return {'error': 'You need to be enrolled in this course to track progress.'}, 403
    
    # For now, we'll just return success
    # In a future implementation, you could add a PDFProgress model similar to VideoProgress
    # to track which PDFs have been viewed by the user
    
    return {'success': True}, 200

@bp.route('/mark-video-completed/<int:video_id>', methods=['POST'])
@login_required
def mark_video_completed(video_id):
    """
    Mark a video as completed via AJAX call
    """
    video = Video.query.get_or_404(video_id)
    
    # Update or create progress record
    progress = VideoProgress.query.filter_by(
        user_id=current_user.id,
        video_id=video_id
    ).first()
    
    if not progress:
        progress = VideoProgress(
            user_id=current_user.id,
            video_id=video_id,
            seconds_watched=video.duration_seconds,
            is_completed=True,
            last_watched_at=datetime.utcnow()
        )
        db.session.add(progress)
    else:
        progress.is_completed = True
        progress.seconds_watched = video.duration_seconds
        progress.last_watched_at = datetime.utcnow()
    
    db.session.commit()
    
    # Check if all videos in the course are completed
    course_id = video.course_id
    all_videos = Video.query.filter_by(course_id=course_id).all()
    completed_videos = VideoProgress.query.filter_by(
        user_id=current_user.id,
        is_completed=True
    ).join(Video).filter(Video.course_id == course_id).count()
    
    all_completed = completed_videos == len(all_videos)
    
    # If all videos are completed, update the enrollment record
    certificate = None
    if all_completed:
        enrollment = UserCourse.query.filter_by(
            user_id=current_user.id,
            course_id=course_id
        ).first()
        
        if enrollment and not enrollment.completed:
            # Mark the course as completed
            enrollment.completed = True
            enrollment.completion_date = datetime.utcnow()
            db.session.commit()
            
            # Get the course object
            course = Course.query.get(course_id)
            
            # Check if this course requires a quiz to be passed
            quiz = Quiz.query.filter_by(course_id=course_id).first()
            
            # If there's no quiz, or it's already been passed, issue a certificate
            quiz_passed = False
            if quiz:
                # Check if the user has passed the quiz
                latest_attempt = QuizAttempt.query.filter_by(
                    user_id=current_user.id,
                    quiz_id=quiz.id,
                    passed=True
                ).first()
                
                if latest_attempt:
                    quiz_passed = True
            
            # If there's no quiz or if the user passed it, issue certificate
            if not quiz or quiz_passed:
                # Attempt to issue a certificate
                from app.utils.certificate import issue_certificate_on_course_completion
                certificate = issue_certificate_on_course_completion(current_user.id, course_id)
            
            # Send course completion email
            from app.utils.email import EmailService
            email_sent = EmailService.send_course_completion_email(current_user, course, certificate)
            if email_sent:
                current_app.logger.info(f"Course completion email sent to: {current_user.email} for course: {course.title}")
            else:
                current_app.logger.warning(f"Failed to send course completion email to: {current_user.email} for course: {course.title}")
    
    return {'success': True, 'all_completed': all_completed}, 200

@bp.route('/update-video-progress/<int:video_id>', methods=['POST'])
@login_required
def update_video_progress(video_id):
    """
    Update video progress via AJAX call
    """
    video = Video.query.get_or_404(video_id)
    
    # Get current time from request
    data = request.get_json()
    if not data or 'current_time' not in data:
        return jsonify({'success': False, 'error': 'Missing current_time parameter'}), 400
    
    try:
        # Ensure current_time is an integer
        current_time = int(float(data['current_time']))
        
        # Log the request for debugging
        current_app.logger.info(f"Updating progress for user {current_user.id}, video {video_id}, time {current_time}")
        
        # Update or create progress record
        progress = VideoProgress.query.filter_by(
            user_id=current_user.id,
            video_id=video_id
        ).first()
        
        if not progress:
            progress = VideoProgress(
                user_id=current_user.id,
                video_id=video_id,
                seconds_watched=current_time,
                is_completed=False,
                last_watched_at=datetime.utcnow()
            )
            db.session.add(progress)
            current_app.logger.info(f"Created new progress record for user {current_user.id}, video {video_id}")
        else:
            # Only update if the new time is greater than the saved time
            if current_time > progress.seconds_watched:
                progress.seconds_watched = current_time
                progress.last_watched_at = datetime.utcnow()
                current_app.logger.info(f"Updated progress to {current_time} seconds for user {current_user.id}, video {video_id}")
            
            # Mark as completed if watched more than 90% of the video
            if video.duration_seconds > 0 and current_time >= video.duration_seconds * 0.9 and not progress.is_completed:
                progress.is_completed = True
                current_app.logger.info(f"Marked video {video_id} as completed for user {current_user.id}")
        
        # Commit the changes and ensure they're saved
        db.session.commit()
        
        # Return success response with updated seconds watched
        return jsonify({
            'success': True, 
            'seconds_watched': progress.seconds_watched,
            'is_completed': progress.is_completed
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating progress: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/video-file/<int:video_id>')
@login_required
def video_file(video_id):
    """
    Serve a video file directly with proper headers for streaming
    """
    # Get the video or return 404
    video = Video.query.get_or_404(video_id)
    
    # Check if the user is enrolled in the course or if video is free or user is admin
    if not current_user.is_admin:
        enrollment = UserCourse.query.filter_by(
            user_id=current_user.id,
            course_id=video.course_id
        ).first()
        
        if not enrollment and not video.is_free:
            abort(403)  # Forbidden
    
    # Get the absolute path to the video file
    video_filename = os.path.basename(video.video_path)
    video_directory = os.path.join(current_app.static_folder, 'uploads', 'videos')
    
    # Log debugging information
    current_app.logger.info(f"Serving video: {video_filename}")
    current_app.logger.info(f"From directory: {video_directory}")
    
    # Check if file exists
    full_path = os.path.join(video_directory, video_filename)
    if not os.path.exists(full_path):
        current_app.logger.error(f"Video file not found: {full_path}")
        abort(404)
        
    # Use send_from_directory with explicit MIME type for better browser compatibility
    return send_from_directory(
        video_directory, 
        video_filename,
        mimetype='video/mp4',
        as_attachment=False,
        conditional=True  # Support for HTTP range requests (important for video seeking)
    )

@bp.route('/pdf-file/<int:pdf_id>')
@login_required
def pdf_file(pdf_id):
    """
    Serve a PDF file directly with proper headers
    """
    # Get the PDF or return 404
    pdf = CoursePDF.query.get_or_404(pdf_id)
    
    # Check if the user is enrolled in the course or user is admin
    if not current_user.is_admin:
        enrollment = UserCourse.query.filter_by(
            user_id=current_user.id,
            course_id=pdf.course_id
        ).first()
        
        if not enrollment:
            abort(403)  # Forbidden
    
    # Get the absolute path to the PDF file
    pdf_filename = os.path.basename(pdf.pdf_path)
    pdf_directory = os.path.join(current_app.static_folder, 'uploads', 'pdfs')
    
    # Log debugging information
    current_app.logger.info(f"Serving PDF: {pdf_filename}")
    current_app.logger.info(f"From directory: {pdf_directory}")
    
    # Check if file exists
    full_path = os.path.join(pdf_directory, pdf_filename)
    if not os.path.exists(full_path):
        current_app.logger.error(f"PDF file not found: {full_path}")
        abort(404)
        
    # Use send_from_directory with explicit MIME type for better browser compatibility
    return send_from_directory(
        pdf_directory, 
        pdf_filename,
        mimetype='application/pdf',
        as_attachment=False
    )
"""
Main blueprint routes
"""
from flask import Blueprint, render_template, redirect, url_for, current_app
from flask_login import current_user, login_required
import os
from sqlalchemy import desc
from app.models import PlatformConfig, UserCourse, Course, Video, VideoProgress

bp = Blueprint('main', __name__)

def is_setup_complete():
    """Check if the setup is already completed"""
    # Check if setup flag file exists
    if os.path.exists(current_app.config['SETUP_FLAG_FILE']):
        return True
    
    # Check if setup is marked as complete in database
    try:
        platform_config = PlatformConfig.query.first()
        if platform_config and platform_config.setup_complete:
            return True
    except Exception as e:
        # If there's an error (like missing table), return False to trigger setup
        current_app.logger.error(f"Database error in is_setup_complete: {str(e)}")
        return False
    
    return False

@bp.route('/')
@bp.route('/index')
def index():
    """
    Main index/home page route
    """
    # Check if setup is complete, if not redirect to installer
    if not is_setup_complete():
        return redirect(url_for('installer.index'))
        
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('main/index.html', title='Home')

@bp.route('/dashboard')
@login_required
def dashboard():
    """
    User dashboard page
    """
    # Get user's enrolled courses with progress
    enrolled_courses = UserCourse.query.filter_by(user_id=current_user.id).all()
    
    # Calculate progress for each enrollment
    for enrollment in enrolled_courses:
        # Add course details to each enrollment
        enrollment.course = Course.query.get(enrollment.course_id)
        
        # Calculate progress based on completed videos
        total_videos = enrollment.course.videos.count()
        if total_videos > 0:
            completed_videos = VideoProgress.query.filter_by(
                user_id=current_user.id, 
                is_completed=True
            ).join(Video).filter(
                Video.course_id==enrollment.course_id
            ).count()
            enrollment.progress_percent = (completed_videos / total_videos) * 100
        else:
            enrollment.progress_percent = 0
    
    # Get recommended courses (excluding ones user is already enrolled in)
    enrolled_course_ids = [e.course_id for e in enrolled_courses]
    recommended_courses = Course.query.filter(
        Course.id.notin_(enrolled_course_ids) if enrolled_course_ids else True,
        Course.is_active == True
    ).order_by(desc(Course.created_at)).limit(3).all()
    
    return render_template(
        'main/dashboard.html', 
        title='Dashboard',
        enrolled_courses=enrolled_courses,
        recommended_courses=recommended_courses
    )

@bp.route('/about')
def about():
    """
    About page route
    """
    return render_template('main/about.html', title='About')
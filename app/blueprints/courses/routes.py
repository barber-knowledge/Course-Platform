"""
Courses blueprint routes
"""
from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from app.models import Course, UserCourse
from app import db

bp = Blueprint('courses', __name__, url_prefix='/courses')

@bp.route('/')
def index():
    """
    List all available courses
    """
    # Query all active courses from the database
    courses = Course.query.filter_by(is_active=True).all()
    return render_template('courses/index.html', title='Available Courses', courses=courses)

@bp.route('/<int:course_id>')
def view(course_id):
    """
    View a specific course
    """
    # Course viewing logic would go here
    return render_template('courses/view.html', title='Course Details', course_id=course_id)

@bp.route('/<int:course_id>/enroll', methods=['GET', 'POST'])
@login_required
def enroll(course_id):
    """
    Enroll in a course
    """
    # Enrollment logic would go here
    return redirect(url_for('courses.view', course_id=course_id))

@bp.route('/enrolled')
@login_required
def enrolled():
    """
    View user's enrolled courses
    """
    # User courses logic would go here
    return render_template('courses/enrolled.html', title='My Courses')

@bp.route('/<int:course_id>/video/<int:video_id>')
@login_required
def video(course_id, video_id):
    """
    Watch a specific video in a course
    """
    # Video viewing logic would go here
    return render_template('courses/video.html', title='Course Video', 
                          course_id=course_id, video_id=video_id)
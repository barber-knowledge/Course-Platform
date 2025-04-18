import os
from datetime import datetime
import uuid
from flask import render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import Course, Quiz, QuizQuestion, QuizAnswer, Video, CoursePDF, User
from app.blueprints.admin import admin
from app import db
from app.extensions import allowed_file
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
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        price = float(request.form.get('price', 0))
        is_active = 'is_published' in request.form  # Changed to match the model field name
        
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
            is_active=is_active,
            image_url=image_url  # Changed from image to image_url
        )
        
        db.session.add(course)
        db.session.commit()
        
        flash('Course created successfully!', 'success')
        return redirect(url_for('admin.courses'))
        
    # Changed to use the form.html template
    return render_template('admin/courses/form.html', course=None)

@admin.route('/courses/<int:course_id>', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    """Edit an existing course"""
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'POST':
        course.title = request.form.get('title')
        course.description = request.form.get('description')
        course.price = float(request.form.get('price', 0))
        course.is_active = 'is_published' in request.form  # Changed to match the model field name
        
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
    return render_template('admin/courses/form.html', course=course)

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

# Platform Settings Route
@admin.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Configure platform settings"""
    from app.models import PlatformConfig
    
    # Get or create platform config
    config = PlatformConfig.query.first()
    if not config:
        config = PlatformConfig()
        db.session.add(config)
        db.session.commit()
    
    if request.method == 'POST':
        config.platform_name = request.form.get('platform_name')
        config.primary_color = request.form.get('primary_color')
        config.secondary_color = request.form.get('secondary_color')
        config.welcome_message = request.form.get('welcome_message')
        
        # Handle logo upload if provided
        if 'logo' in request.files and request.files['logo'].filename:
            try:
                logo_file = request.files['logo']
                filename = secure_filename(f"{uuid.uuid4()}_{logo_file.filename}")
                upload_folder = os.path.join(current_app.static_folder, 'uploads', 'logos')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                logo_path = os.path.join(upload_folder, filename)
                logo_file.save(logo_path)
                config.logo_path = os.path.join('uploads', 'logos', filename)
            except Exception as e:
                flash(f'Failed to upload logo: {str(e)}', 'danger')
                current_app.logger.error(f'Logo upload failed: {str(e)}')
        
        # Stripe settings
        config.stripe_secret_key = request.form.get('stripe_secret_key')
        config.stripe_publishable_key = request.form.get('stripe_publishable_key')
        config.stripe_enabled = 'stripe_enabled' in request.form
        
        try:
            db.session.commit()
            flash('Platform settings saved successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to save settings: {str(e)}', 'danger')
            current_app.logger.error(f'Failed to save platform config: {str(e)}')
    
    return render_template('admin/settings/index.html', config=config)
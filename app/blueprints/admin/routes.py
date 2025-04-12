import os
from datetime import datetime
import uuid
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import Course, Quiz, QuizQuestion, QuizAnswer, Video, CoursePDF, User
from app.blueprints.admin import admin
from app import db
from app.extensions import allowed_file

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
    
    return render_template('admin/index.html', 
                          courses_count=courses_count,
                          quizzes_count=quizzes_count,
                          videos_count=videos_count,
                          pdfs_count=pdfs_count,
                          users_count=users_count)

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
        is_published = 'is_published' in request.form
        
        # Handle image upload
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and allowed_file(image_file.filename, ['jpg', 'jpeg', 'png']):
                filename = secure_filename(f"{uuid.uuid4()}_{image_file.filename}")
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'courses', filename)
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                image_file.save(image_path)
                image_url = f"/static/uploads/courses/{filename}"
            else:
                image_url = None
        else:
            image_url = None
            
        course = Course(
            title=title,
            description=description,
            price=price,
            image_url=image_url,
            is_published=is_published
        )
        
        db.session.add(course)
        db.session.commit()
        
        flash('Course created successfully!', 'success')
        return redirect(url_for('admin.courses'))
        
    return render_template('admin/courses/new.html')

@admin.route('/courses/<int:course_id>', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    """Edit an existing course"""
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'POST':
        course.title = request.form.get('title')
        course.description = request.form.get('description')
        course.price = float(request.form.get('price', 0))
        course.is_published = 'is_published' in request.form
        
        # Handle image upload
        if 'image' in request.files and request.files['image'].filename:
            image_file = request.files['image']
            if allowed_file(image_file.filename, ['jpg', 'jpeg', 'png']):
                filename = secure_filename(f"{uuid.uuid4()}_{image_file.filename}")
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'courses', filename)
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                image_file.save(image_path)
                course.image_url = f"/static/uploads/courses/{filename}"
        
        db.session.commit()
        flash('Course updated successfully!', 'success')
        return redirect(url_for('admin.courses'))
        
    return render_template('admin/courses/edit.html', course=course)

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
        video_url = request.form.get('video_url')
        sequence_order = int(request.form.get('sequence_order', 1))
        duration = int(request.form.get('duration', 0))
        
        # Create a new video
        video = Video(
            course_id=course_id,
            title=title,
            description=description,
            video_url=video_url,
            sequence_order=sequence_order,
            duration=duration
        )
        
        db.session.add(video)
        db.session.commit()
        
        flash('Video added successfully!', 'success')
        return redirect(url_for('admin.videos', course_id=course_id))
        
    return render_template('admin/videos/new.html', course=course)

@admin.route('/videos/<int:video_id>', methods=['GET', 'POST'])
@login_required
def edit_video(video_id):
    """Edit a video"""
    video = Video.query.get_or_404(video_id)
    
    if request.method == 'POST':
        video.title = request.form.get('title')
        video.description = request.form.get('description')
        video.video_url = request.form.get('video_url')
        video.sequence_order = int(request.form.get('sequence_order', 1))
        video.duration = int(request.form.get('duration', 0))
        
        db.session.commit()
        
        flash('Video updated successfully!', 'success')
        return redirect(url_for('admin.videos', course_id=video.course_id))
        
    return render_template('admin/videos/edit.html', video=video)

@admin.route('/videos/<int:video_id>/delete', methods=['POST'])
@login_required
def delete_video(video_id):
    """Delete a video"""
    video = Video.query.get_or_404(video_id)
    course_id = video.course_id
    
    db.session.delete(video)
    db.session.commit()
    
    flash('Video deleted successfully!', 'success')
    return redirect(url_for('admin.videos', course_id=course_id))

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
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        pass_percentage = int(request.form.get('pass_percentage', 70))
        
        # Create the quiz
        quiz = Quiz(
            course_id=course_id,
            title=title,
            description=description,
            pass_percentage=pass_percentage
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
        quiz.pass_percentage = int(request.form.get('pass_percentage', 70))
        
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
        question_type = request.form.get('question_type', 'multiple_choice')
        points = int(request.form.get('points', 1))
        
        # Create the question
        question = QuizQuestion(
            quiz_id=quiz_id,
            question_text=question_text,
            question_type=question_type,
            points=points
        )
        
        db.session.add(question)
        db.session.commit()
        
        # Process answers
        if question_type in ['multiple_choice', 'single_choice']:
            answers = request.form.getlist('answer_text[]')
            is_correct_list = request.form.getlist('is_correct[]')
            
            for i, answer_text in enumerate(answers):
                if answer_text.strip():
                    is_correct = str(i) in is_correct_list
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
        
        # Delete existing answers
        QuizAnswer.query.filter_by(question_id=question_id).delete()
        
        # Process answers
        if question.question_type in ['multiple_choice', 'single_choice']:
            answers = request.form.getlist('answer_text[]')
            is_correct_list = request.form.getlist('is_correct[]')
            
            for i, answer_text in enumerate(answers):
                if answer_text.strip():
                    is_correct = str(i) in is_correct_list
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
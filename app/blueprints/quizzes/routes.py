"""
Quizzes blueprint routes
"""
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash, current_app
from flask_login import login_required, current_user
from app.models import Quiz, QuizQuestion, QuizAnswer, QuizAttempt, Course, UserCourse, Video, VideoProgress, Certificate
from app.utils.email import EmailService
from app.utils.certificate import generate_certificate
from app import db
from datetime import datetime
from sqlalchemy import func

bp = Blueprint('quizzes', __name__, url_prefix='/quizzes')

@bp.route('/<int:quiz_id>')
@login_required
def take(quiz_id):
    """
    Take a quiz
    """
    try:
        # Get the quiz
        quiz = Quiz.query.get_or_404(quiz_id)
        course = Course.query.get_or_404(quiz.course_id)
        
        # Check if user is enrolled in the course
        enrollment = UserCourse.query.filter_by(user_id=current_user.id, course_id=course.id).first()
        if not enrollment and not current_user.is_admin:
            flash('You must be enrolled in this course to take the quiz.', 'danger')
            return redirect(url_for('courses.view', course_id=course.id))
        
        # Get all questions for the quiz
        questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).order_by(QuizQuestion.sequence_order).all()
        
        # Make sure there are questions
        if not questions:
            flash("This quiz doesn't have any questions yet. Please try again later.", "warning")
            return redirect(url_for('courses.view', course_id=course.id))
        
        # Prepare the question list with answers as actual lists, not query objects
        prepared_questions = []
        for question in questions:
            # Count answers using count() instead of len(), which works with AppenderQuery
            answer_count = QuizAnswer.query.filter_by(question_id=question.id).count()
            
            if answer_count != 4:
                flash(f"Question {question.id} has {answer_count} answers instead of 4. Please contact an administrator.", "warning")
                return redirect(url_for('courses.view', course_id=course.id))
            
            # Create a new object with all the attributes of the original question
            question_dict = {
                'id': question.id,
                'quiz_id': question.quiz_id,
                'question_text': question.question_text,
                'question_type': question.question_type,
                'points': question.points,
                'sequence_order': question.sequence_order,
                # Explicitly get answers as a list, not a query object
                'answers': QuizAnswer.query.filter_by(question_id=question.id).all()
            }
            prepared_questions.append(question_dict)
        
        return render_template('quizzes/take.html', quiz=quiz, questions=prepared_questions)
    except Exception as e:
        # Log the error for debugging
        import traceback
        traceback.print_exc()
        flash(f"An error occurred while loading this quiz: {str(e)}", "danger")
        return redirect(url_for('main.index'))

@bp.route('/<int:quiz_id>/submit', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    """
    Submit a quiz for grading
    """
    # Get the quiz
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Get all questions for the quiz
    questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).all()
    
    # Calculate score
    total_points = sum(q.points for q in questions)
    earned_points = 0
    
    for question in questions:
        # Get user's answer for this question
        selected_answer_index = request.form.get(f'q{question.id}')
        
        # If no answer was selected, skip this question
        if selected_answer_index is None:
            continue
        
        # Convert to integer
        selected_answer_index = int(selected_answer_index)
        
        # Get all answers for this question
        answers = QuizAnswer.query.filter_by(question_id=question.id).all()
        
        # Find the correct answer
        for i, answer in enumerate(answers):
            if answer.is_correct and i == selected_answer_index:
                earned_points += question.points
                break
    
    # Calculate percentage score
    percentage_score = (earned_points / total_points) * 100 if total_points > 0 else 0
    
    # Determine if user passed the quiz
    passed = percentage_score >= quiz.passing_percentage
    
    # Record the quiz attempt
    quiz_attempt = QuizAttempt(
        user_id=current_user.id,
        quiz_id=quiz_id,
        score=round(percentage_score),
        passed=passed,
        completed_at=datetime.utcnow()
    )
    db.session.add(quiz_attempt)
    
    # If the user passed the quiz, mark the course as completed if all videos are watched
    # and issue a certificate if appropriate
    certificate = None
    if passed:
        course = Course.query.get(quiz.course_id)
        
        # Check if all videos have been completed
        all_videos = Video.query.filter_by(course_id=course.id).all()
        completed_videos = VideoProgress.query.filter_by(
            user_id=current_user.id,
            is_completed=True
        ).join(Video).filter(Video.course_id == course.id).count()
        
        all_videos_completed = completed_videos == len(all_videos)
        
        # Get the enrollment record
        enrollment = UserCourse.query.filter_by(
            user_id=current_user.id,
            course_id=course.id
        ).first()
        
        # Update enrollment to completed if all videos are completed and quiz is passed
        if enrollment and all_videos_completed and not enrollment.completed:
            enrollment.completed = True
            enrollment.completion_date = datetime.utcnow()
            db.session.commit()
            
        # If the course is marked as completed and has certificate enabled, 
        # generate certificate if one doesn't exist
        if enrollment and enrollment.completed and course.has_certificate:
            # Check if a certificate already exists
            existing_certificate = Certificate.query.filter_by(
                user_id=current_user.id,
                course_id=course.id
            ).first()
            
            if not existing_certificate:
                # Issue a certificate
                from app.utils.certificate import issue_certificate_on_course_completion
                certificate = issue_certificate_on_course_completion(current_user.id, course.id)
                if certificate:
                    flash(f'Congratulations on completing {course.title}! Your certificate is ready.', 'success')
                    return redirect(url_for('certificates.view', course_id=course.id))
                else:
                    flash(f'Congratulations on completing {course.title}!', 'success')
                    return redirect(url_for('courses.view', course_id=course.id))
            else:
                flash(f'Quiz passed! Your score: {round(percentage_score)}%', 'success')
    
    db.session.commit()
    
    # Send quiz results email
    email_sent = EmailService.send_quiz_results_email(current_user, quiz, quiz_attempt)
    if email_sent:
        current_app.logger.info(f"Quiz results email sent to: {current_user.email} for quiz: {quiz.title}")
    else:
        current_app.logger.warning(f"Failed to send quiz results email to: {current_user.email} for quiz: {quiz.title}")
    
    # Redirect to results page
    return redirect(url_for('quizzes.results', attempt_id=quiz_attempt.id))

@bp.route('/attempt/<int:attempt_id>/results')
@login_required
def results(attempt_id):
    """
    View quiz results
    """
    # Get the attempt
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    # Make sure the user is viewing their own result
    if attempt.user_id != current_user.id:
        flash('You are not authorized to view these results.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get the quiz
    quiz = Quiz.query.get(attempt.quiz_id)
    
    return render_template('quizzes/results.html', 
                          attempt=attempt, 
                          quiz=quiz,
                          passed=attempt.passed,
                          score=attempt.score)

@bp.route('/history')
@login_required
def history():
    """
    View quiz attempt history
    """
    # Get all quiz attempts for the current user
    attempts = QuizAttempt.query.filter_by(user_id=current_user.id).order_by(QuizAttempt.completed_at.desc()).all()
    
    return render_template('quizzes/history.html', attempts=attempts)
"""
Quizzes blueprint routes
"""
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from flask_login import login_required, current_user
from app.models import Quiz, QuizQuestion, QuizAnswer, QuizAttempt, Course, UserCourse
from app import db
from datetime import datetime
from sqlalchemy import func

bp = Blueprint('quizzes', __name__, url_prefix='/quizzes')

@bp.route('/<int:quiz_id>')
@login_required
def take_quiz(quiz_id):
    """
    Take a quiz
    """
    # Get the quiz
    quiz = Quiz.query.get_or_404(quiz_id)
    course = Course.query.get_or_404(quiz.course_id)
    
    # Check if user is enrolled in the course
    enrollment = UserCourse.query.filter_by(user_id=current_user.id, course_id=course.id).first()
    if not enrollment:
        flash('You must be enrolled in this course to take the quiz.', 'danger')
        return redirect(url_for('courses.view', course_id=course.id))
    
    # Get all questions for the quiz
    questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).order_by(QuizQuestion.sequence_order).all()
    
    # For each question, load its 4 answers
    for question in questions:
        question.answers = QuizAnswer.query.filter_by(question_id=question.id).all()
        # Make sure we have exactly 4 answers
        if len(question.answers) != 4:
            flash(f"Question {question.id} doesn't have exactly 4 answers. Please contact an administrator.", "danger")
            return redirect(url_for('courses.view', course_id=course.id))
    
    return render_template('quizzes/take.html', quiz=quiz, questions=questions)

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
    
    # If this is the user's first successful attempt and the course has certificates,
    # generate a certificate (this would be implemented elsewhere)
    
    db.session.commit()
    
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
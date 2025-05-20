"""
Auth blueprint routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import User
from app.utils.email import EmailService
from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login route
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Debug information
        current_app.logger.info("Login attempt - Form data received")
        
        email = request.form.get('email')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        # Add detailed debugging
        current_app.logger.debug(f"Login details - Email: {email}, Remember: {remember}")
        
        if not email or not password:
            error_msg = 'Please enter both email and password.'
            current_app.logger.warning(f"Login failed: {error_msg}")
            flash(error_msg, 'danger')
            return redirect(url_for('auth.login'))
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            error_msg = 'No account found with this email address.'
            current_app.logger.warning(f"Login failed: {error_msg}")
            flash('Invalid email or password.', 'danger')  # Generic message for security
            return redirect(url_for('auth.login'))
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            current_app.logger.info(f"Login successful for user: {email}")
            flash('Login successful!', 'success')
            
            # If there was a page the user was trying to access, redirect there
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            return redirect(url_for('main.dashboard'))
        else:
            error_msg = 'Invalid password for user.'
            current_app.logger.warning(f"Login failed: {error_msg}")
            flash('Invalid email or password.', 'danger')  # Generic message for security
    
    return render_template('auth/login.html', title='Sign In')

@bp.route('/logout')
def logout():
    """
    User logout route
    """
    if current_user.is_authenticated:
        current_app.logger.info(f"Logout for user: {current_user.email}")
    
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration route
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Debug information
        current_app.logger.info("Registration attempt - Form data received")
        
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        terms = 'terms' in request.form
        
        # Form validation
        error = None
        if not name or not email or not password:
            error = 'All fields are required.'
        elif password != confirm_password:
            error = 'Passwords do not match.'
        elif len(password) < 8:
            error = 'Password must be at least 8 characters long.'
        elif not terms:
            error = 'You must agree to the terms and conditions.'
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            error = 'Email address already registered.'
        
        if error:
            current_app.logger.warning(f"Registration failed: {error}")
            flash(error, 'danger')
            return redirect(url_for('auth.register'))
        
        # Create new user
        try:
            new_user = User(name=name, email=email)
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            current_app.logger.info(f"Registration successful for: {email}")
            
            # Send welcome email
            email_sent = EmailService.send_user_registration_email(new_user)
            if email_sent:
                current_app.logger.info(f"Welcome email sent to: {email}")
            else:
                current_app.logger.warning(f"Failed to send welcome email to: {email}")
            
            # Log in the new user
            login_user(new_user)
            flash('Registration successful! Welcome to the platform.', 'success')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration error: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'danger')
            return redirect(url_for('auth.register'))
    
    return render_template('auth/register.html', title='Register')

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    User profile route
    """
    return render_template('auth/profile.html', title='Profile')

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """
    Forgot password route - allows users to request a password reset email
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Please enter your email address.', 'danger')
            return redirect(url_for('auth.forgot_password'))
        
        user = User.query.filter_by(email=email).first()
        
        # Always show the same message whether user exists or not for security reasons
        if user:
            # Send password reset email
            email_sent = EmailService.send_password_reset_email(user)
            
            if email_sent:
                current_app.logger.info(f"Password reset email sent to: {email}")
            else:
                current_app.logger.warning(f"Failed to send password reset email to: {email}")
                
        flash('If an account exists with this email, you will receive password reset instructions.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html', title='Forgot Password')

@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Reset password route - allows users to set a new password using a valid token
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # Verify token and get user
    user = User.query.filter(User.reset_password_token == token).first()
    token_valid = False
    
    if user:
        # Check if token is expired
        if user.reset_token_expires_at and user.reset_token_expires_at > datetime.utcnow():
            token_valid = True
            
    if not token_valid:
        current_app.logger.warning(f"Invalid or expired reset token used: {token}")
        # We'll handle the invalid token case in the template
        return render_template('auth/reset_password.html', token_valid=False, token=token)
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate passwords
        if not password or not confirm_password:
            flash('Please enter both password fields.', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
            
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
            
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        # Update user password
        try:
            user.set_password(password)
            # Clear the reset token
            user.clear_reset_token()
            
            db.session.commit()
            
            current_app.logger.info(f"Password reset successful for user: {user.email}")
            flash('Your password has been reset successfully. You can now log in with your new password.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Password reset error: {str(e)}")
            flash('An error occurred while resetting your password. Please try again.', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
    
    return render_template('auth/reset_password.html', token_valid=token_valid, token=token)
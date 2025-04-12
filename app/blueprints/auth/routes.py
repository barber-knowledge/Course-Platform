"""
Auth blueprint routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import User
from werkzeug.security import generate_password_hash, check_password_hash

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login route
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        if not email or not password:
            flash('Please enter email and password.', 'danger')
            return redirect(url_for('auth.login'))
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash('Login successful!', 'success')
            
            # If there was a page the user was trying to access, redirect there
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html', title='Sign In')

@bp.route('/logout')
def logout():
    """
    User logout route
    """
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
            flash(error, 'danger')
            return redirect(url_for('auth.register'))
        
        # Create new user
        try:
            new_user = User(name=name, email=email)
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            # Log in the new user
            login_user(new_user)
            flash('Registration successful! Welcome to the platform.', 'success')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.session.rollback()
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
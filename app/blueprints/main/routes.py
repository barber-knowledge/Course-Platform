"""
Main blueprint routes
"""
from flask import Blueprint, render_template, redirect, url_for, current_app
from flask_login import current_user, login_required
import os
from app.models import PlatformConfig

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
    return render_template('main/dashboard.html', title='Dashboard')

@bp.route('/about')
def about():
    """
    About page route
    """
    return render_template('main/about.html', title='About')
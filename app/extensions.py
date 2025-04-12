"""
Flask extensions for the modular course platform.

This file initializes all Flask extensions used across the application:
- SQLAlchemy for database ORM
- Flask-Login for user authentication
- Flask-Mail for sending emails
- Flask-Migrate for database migrations
- Flask-WTF for form handling and CSRF protection
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

# Initialize SQLAlchemy
db = SQLAlchemy()

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Initialize Flask-Mail
mail = Mail()

# Initialize Flask-Migrate
migrate = Migrate()

# Initialize Flask-WTF CSRF protection
csrf = CSRFProtect()

def allowed_file(filename, allowed_extensions):
    """
    Check if a filename has an allowed extension
    
    Args:
        filename (str): The name of the file to check
        allowed_extensions (list): List of allowed file extensions (without dots)
    
    Returns:
        bool: True if the file has an allowed extension, False otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Import models to ensure they're registered with SQLAlchemy
# This import is at the bottom to avoid circular imports
# from app import models
"""
Configuration settings for the modular course platform.

This file defines hardcoded configuration classes that can be used with the Flask application.

Copilot Instruction:
Use SQLAlchemy to connect to a **remote MariaDB instance**, not localhost.

- IP: 66.179.241.151
- Port: 3306
- DB: admin_
- User: admin_modularce
- Password: 320eK~lw8

Use pymysql driver in the format:
mysql+pymysql://<user>:<pass>@<host>:<port>/<database>
"""

import os
from dotenv import load_dotenv

# Base directory of the application
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base configuration class with hardcoded settings."""
    
    # Flask settings
    SECRET_KEY = 'dev-key-please-change-in-production'
    
    # Database connection details (hardcoded for testing)
    # Hostname / IP: This is the public IP of the database server
    DB_HOST = 'courseapp.cxi0cykmat4u.us-east-2.rds.amazonaws.com'
    
    # Port: Default MariaDB/MySQL port
    DB_PORT = 3306
    
    # Database name
    DB_NAME = 'courseapp'
    
    # Username to authenticate with
    DB_USER = 'admin'
    
    # Password for that user
    DB_PASSWORD = '3d7j*E%xV*VK#*t787'
    
    # SQLAlchemy URI (MySQL + PyMySQL driver)
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-Mail settings - Hardcoded mail settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'youremail@gmail.com'
    MAIL_PASSWORD = 'your-email-password'
    MAIL_DEFAULT_SENDER = 'youremail@gmail.com'
    
    # File upload settings
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    ALLOWED_EXTENSIONS = 'pdf,mp4,webm,jpg,jpeg,png'
    
    # Stripe settings - Hardcoded Stripe keys
    STRIPE_SECRET_KEY = 'your-stripe-secret-key'
    STRIPE_PUBLISHABLE_KEY = 'your-stripe-publishable-key'
    STRIPE_WEBHOOK_SECRET = ''  # Leave empty for now, will be set up later
    
    # Setup flag file path
    SETUP_FLAG_FILE = os.path.join(basedir, '.setup_done')

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    
    @classmethod
    def init_app(cls, app):
        # Log to file in production
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler('logs/modular_course.log',
                                          maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Modular Course Platform startup')

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Dictionary mapping environment names to configuration classes
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

"""
Initialize a modular Flask app using the application factory pattern.

The app is a full-stack learning platform built with Flask. It supports:
- SQLAlchemy (MariaDB)
- Flask-Login
- Flask-Mail
- Flask-WTF for CSRF protection
- Modular blueprints: auth, main, courses, quizzes, certificates, installer
- Config loading from instance folder or .env
"""

import os
import json
from flask import Flask, render_template
from .extensions import db, login_manager, mail, migrate, csrf
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Initialize basic extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.login_view = 'auth.login'

    # Register blueprints
    from .blueprints.auth.routes import bp as auth_bp
    from .blueprints.main.routes import bp as main_bp
    from .blueprints.courses.routes import bp as courses_bp
    from .blueprints.quizzes.routes import bp as quizzes_bp
    from .blueprints.certificates.routes import bp as cert_bp
    from .blueprints.installer.routes import bp as installer_bp
    from .blueprints.admin.routes import admin as admin_bp
    from .blueprints.payments import bp as payments_bp
    from .blueprints.products import bp as products_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(quizzes_bp)
    app.register_blueprint(cert_bp)
    app.register_blueprint(installer_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(products_bp)
    
    # Configure Flask-Mail with database settings
    with app.app_context():
        try:
            from app.models import PlatformConfig
            config = PlatformConfig.get_config()
            
            # Only override if SMTP is enabled and configured in database
            if config.smtp_enabled and config.smtp_server:
                app.logger.info(f"Loading email configuration from database...")
                
                # Clear any existing mail configuration
                for key in list(app.config.keys()):
                    if key.startswith('MAIL_'):
                        del app.config[key]
                
                # Set mail configuration from database
                app.config['MAIL_SERVER'] = config.smtp_server
                app.config['MAIL_PORT'] = config.smtp_port
                app.config['MAIL_USERNAME'] = config.smtp_username
                app.config['MAIL_PASSWORD'] = config.smtp_password
                app.config['MAIL_USE_TLS'] = bool(config.smtp_use_tls)
                app.config['MAIL_USE_SSL'] = bool(config.smtp_use_ssl)
                app.config['MAIL_DEFAULT_SENDER'] = config.smtp_default_sender
                
                app.logger.info(f"Email configured with database settings: {config.smtp_server}:{config.smtp_port}")
                app.logger.info(f"SMTP Username: {config.smtp_username}")
                app.logger.info(f"TLS Enabled: {bool(config.smtp_use_tls)}")
                app.logger.info(f"SSL Enabled: {bool(config.smtp_use_ssl)}")
            else:
                app.logger.warning("Email not configured in database or disabled. Using default configuration.")
        except Exception as e:
            app.logger.error(f"Failed to configure mail from database: {str(e)}")
    
    # Initialize mail AFTER configuring settings
    mail.init_app(app)

    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Register custom filters
    @app.template_filter('from_json')
    def from_json(value):
        """Convert a JSON string to a Python object"""
        try:
            return json.loads(value) if value else []
        except:
            return []

    # Add context processor for platform configuration
    @app.context_processor
    def inject_platform_config():
        from app.models import PlatformConfig
        config = PlatformConfig.query.first()
        if not config:
            config = PlatformConfig()
            db.session.add(config)
            db.session.commit()
        return dict(config=config)

    # Ensure the uploads directories exist
    with app.app_context():
        create_upload_dirs(app)
        
        # Initialize default email templates if they don't exist
        from app.models import EmailTemplate
        EmailTemplate.init_default_templates()

    return app

def create_upload_dirs(app):
    """Create directories for file uploads"""
    static_folder = app.static_folder
    upload_dirs = [
        os.path.join(static_folder, 'uploads'),
        os.path.join(static_folder, 'uploads', 'videos'),
        os.path.join(static_folder, 'uploads', 'pdfs'),
        os.path.join(static_folder, 'uploads', 'courses'),
        os.path.join(static_folder, 'uploads', 'products'),
        os.path.join(static_folder, 'uploads', 'logos'),
        os.path.join(static_folder, 'uploads', 'popups')
    ]

    for directory in upload_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)
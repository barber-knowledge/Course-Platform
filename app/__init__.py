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

from flask import Flask
from .extensions import db, login_manager, mail, migrate, csrf
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Register blueprints
    from .blueprints.auth.routes import bp as auth_bp
    from .blueprints.main.routes import bp as main_bp
    from .blueprints.courses.routes import bp as courses_bp
    from .blueprints.quizzes.routes import bp as quizzes_bp
    from .blueprints.certificates.routes import bp as cert_bp
    from .blueprints.installer.routes import bp as installer_bp
    from .blueprints.admin.routes import admin as admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(quizzes_bp)
    app.register_blueprint(cert_bp)
    app.register_blueprint(installer_bp)
    app.register_blueprint(admin_bp)

    return app
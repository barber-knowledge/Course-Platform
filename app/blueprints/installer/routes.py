"""
Installer blueprint routes for the setup wizard
"""
from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request
from flask_login import login_required, current_user, login_user
from werkzeug.utils import secure_filename
from app import db
from app.models import User, PlatformConfig
import os
import uuid

bp = Blueprint('installer', __name__, url_prefix='/installer')

def is_setup_complete():
    """Check if the setup is already completed"""
    # Check if setup flag file exists
    if os.path.exists(current_app.config['SETUP_FLAG_FILE']):
        return True
    
    # Check if setup is marked as complete in database
    platform_config = PlatformConfig.query.first()
    if platform_config and platform_config.setup_complete:
        return True
    
    return False

def mark_setup_complete():
    """Mark the setup as completed"""
    # Create the setup flag file
    with open(current_app.config['SETUP_FLAG_FILE'], 'w') as f:
        f.write('setup_complete')
    
    # Set setup_complete in the database
    platform_config = PlatformConfig.query.first()
    if not platform_config:
        platform_config = PlatformConfig()
        db.session.add(platform_config)
    
    platform_config.setup_complete = True
    db.session.commit()

@bp.before_request
def check_setup():
    """Redirect to dashboard if setup is already completed, except for specific routes"""
    # Allow access to create_admin even if setup is complete
    if is_setup_complete() and request.endpoint not in ['installer.setup_complete', 'installer.create_admin']: 
        flash('Setup has already been completed. Admin users can be managed in the Admin Dashboard.', 'info') # Updated flash message
        # Redirect to admin user management or dashboard if available, otherwise main index
        if current_user.is_authenticated and current_user.is_admin:
             # Assuming you have an admin route for user management, e.g., 'admin.users'
             # return redirect(url_for('admin.users')) 
             return redirect(url_for('admin.index')) # Or redirect to admin dashboard
        return redirect(url_for('main.index'))

@bp.route('/')
def index():
    """Setup wizard starting point"""
    # Check if there are any admin users
    admin_exists = User.query.filter_by(is_admin=True).first() is not None
    
    # Check if database connection works
    db_connected = True
    try:
        db.session.execute('SELECT 1')
    except Exception:
        db_connected = False
    
    # Check if platform config exists
    platform_config = PlatformConfig.query.first()
    
    return render_template('installer/index.html', 
                          admin_exists=admin_exists, 
                          db_connected=db_connected,
                          platform_config=platform_config)

@bp.route('/setup-database')
def setup_database():
    """Set up or reset database tables"""
    try:
        # Create all tables defined in our models
        db.create_all()
        flash('Database setup completed successfully.', 'success')
    except Exception as e:
        flash(f'Database setup failed: {str(e)}', 'danger')
    
    return redirect(url_for('installer.index'))

@bp.route('/create-admin', methods=['GET', 'POST'])
def create_admin():
    """Create initial or additional admin user""" # Updated docstring
    # No need to check is_setup_complete() here anymore due to check_setup modification
    
    admin_exists = User.query.filter_by(is_admin=True).first() is not None

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not name or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('installer.create_admin'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('installer.create_admin'))
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('User with this email already exists.', 'danger')
            return redirect(url_for('installer.create_admin'))
        
        # Create new admin user
        user = User(name=name, email=email, is_admin=True)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Modify flash message based on whether it's the first admin or an additional one
        if not admin_exists:
            flash('Initial admin user created successfully! You can now log in.', 'success')
            # Log in the newly created admin automatically for the first time
            login_user(user) 
            return redirect(url_for('installer.platform_config')) # Redirect to next step if first admin
        else:
            flash('New admin user created successfully!', 'success')
            # Redirect to login or admin user list after creating additional admins
            return redirect(url_for('auth.login')) 

    return render_template('installer/create_admin.html', admin_exists=admin_exists)

@bp.route('/platform-config', methods=['GET', 'POST'])
def platform_config():
    """Configure platform settings"""
    # Get or create platform config
    config = PlatformConfig.query.first()
    if not config:
        config = PlatformConfig()
        db.session.add(config)
        db.session.commit()
    
    # Ensure upload directories exist
    upload_dirs = [
        os.path.join(current_app.static_folder, 'uploads'),
        os.path.join(current_app.static_folder, 'uploads', 'logos'),
        os.path.join(current_app.static_folder, 'uploads', 'pdfs'),
        os.path.join(current_app.static_folder, 'uploads', 'courses')
    ]
    for directory in upload_dirs:
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
        except Exception as e:
            flash(f'Failed to create upload directory: {str(e)}', 'danger')
            current_app.logger.error(f'Failed to create directory {directory}: {str(e)}')
    
    if request.method == 'POST':
        config.platform_name = request.form.get('platform_name')
        config.primary_color = request.form.get('primary_color')
        config.secondary_color = request.form.get('secondary_color')
        config.welcome_message = request.form.get('welcome_message')
        
        # Handle logo upload if provided
        if 'logo' in request.files and request.files['logo'].filename:
            try:
                logo_file = request.files['logo']
                filename = secure_filename(f"{uuid.uuid4()}_{logo_file.filename}")
                upload_folder = os.path.join(current_app.static_folder, 'uploads', 'logos')
                logo_path = os.path.join(upload_folder, filename)
                logo_file.save(logo_path)
                config.logo_path = os.path.join('uploads', 'logos', filename)
            except Exception as e:
                flash(f'Failed to upload logo: {str(e)}', 'danger')
                current_app.logger.error(f'Logo upload failed: {str(e)}')
        
        try:
            db.session.commit()
            flash('Platform configuration saved successfully.', 'success')
            return redirect(url_for('installer.stripe_config'))
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to save configuration: {str(e)}', 'danger')
            current_app.logger.error(f'Failed to save platform config: {str(e)}')
    
    return render_template('installer/platform_config.html', config=config)

@bp.route('/stripe-config', methods=['GET', 'POST'])
def stripe_config():
    """Configure Stripe integration"""
    # Get or create platform config
    config = PlatformConfig.query.first()
    if not config:
        config = PlatformConfig()
        db.session.add(config)
        db.session.commit()
    
    if request.method == 'POST':
        config.stripe_secret_key = request.form.get('stripe_secret_key')
        config.stripe_publishable_key = request.form.get('stripe_publishable_key')
        config.stripe_enabled = request.form.get('stripe_enabled') == 'on'
        
        db.session.commit()
        flash('Stripe configuration saved successfully.', 'success')
        return redirect(url_for('installer.setup_complete'))
    
    return render_template('installer/stripe_config.html', config=config)

@bp.route('/setup-complete')
def setup_complete():
    """Final setup step - mark setup as complete"""
    # Mark setup as complete
    mark_setup_complete()
    
    flash('Setup completed successfully! You can now start using the platform.', 'success')
    return render_template('installer/setup_complete.html')
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
    if is_setup_complete() and request.endpoint != 'installer.setup_complete':
        flash('Setup has already been completed.', 'info')
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
    """Create initial admin user"""
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
        
        # Log in the new admin
        login_user(user)
        
        flash('Admin user created successfully.', 'success')
        return redirect(url_for('installer.platform_config'))
    
    return render_template('installer/create_admin.html')

@bp.route('/platform-config', methods=['GET', 'POST'])
def platform_config():
    """Configure platform settings"""
    # Get or create platform config
    config = PlatformConfig.query.first()
    if not config:
        config = PlatformConfig()
        db.session.add(config)
        db.session.commit()
    
    if request.method == 'POST':
        config.platform_name = request.form.get('platform_name')
        config.primary_color = request.form.get('primary_color')
        config.secondary_color = request.form.get('secondary_color')
        config.welcome_message = request.form.get('welcome_message')
        
        # Handle logo upload if provided
        if 'logo' in request.files and request.files['logo'].filename:
            logo_file = request.files['logo']
            filename = secure_filename(f"{uuid.uuid4()}_{logo_file.filename}")
            upload_folder = os.path.join(current_app.static_folder, 'uploads', 'logos')
            
            # Create folder if it doesn't exist
            os.makedirs(upload_folder, exist_ok=True)
            
            # Save the file
            logo_path = os.path.join(upload_folder, filename)
            logo_file.save(logo_path)
            
            # Save the relative path in the database
            config.logo_path = os.path.join('uploads', 'logos', filename)
        
        db.session.commit()
        flash('Platform configuration saved successfully.', 'success')
        return redirect(url_for('installer.stripe_config'))
    
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
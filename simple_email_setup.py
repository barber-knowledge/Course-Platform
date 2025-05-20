"""
A simple script to configure email settings in the SQLite database
"""
import os
import sqlite3
import json

# Database file path
DB_PATH = os.path.join('instance', 'app.db')

# Email configuration 
CONFIG = {
    'smtp_server': 'smtp.mailgun.org',
    'smtp_port': 587,
    'smtp_username': 'example@mail.example.com',
    'smtp_password': 'your-mailgun-api-key-here',
    'smtp_use_tls': 1,
    'smtp_use_ssl': 0,
    'smtp_default_sender': 'example@mail.example.com',
    'smtp_enabled': 1
}

def configure_email():
    """Configure email settings in the SQLite database"""
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at {DB_PATH}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if platform_config table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='platform_config'")
        if not cursor.fetchone():
            print("Creating platform_config table...")
            cursor.execute('''
            CREATE TABLE platform_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform_name TEXT DEFAULT 'Modular Course Platform',
                primary_color TEXT DEFAULT '#4a6cf7',
                secondary_color TEXT DEFAULT '#6c757d',
                logo_path TEXT,
                welcome_message TEXT,
                setup_complete INTEGER DEFAULT 0,
                stripe_secret_key TEXT,
                stripe_publishable_key TEXT,
                stripe_enabled INTEGER DEFAULT 0,
                smtp_server TEXT,
                smtp_port INTEGER,
                smtp_username TEXT,
                smtp_password TEXT,
                smtp_use_tls INTEGER DEFAULT 1,
                smtp_use_ssl INTEGER DEFAULT 0,
                smtp_default_sender TEXT,
                smtp_enabled INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            # Insert default record
            cursor.execute('''
            INSERT INTO platform_config (platform_name, primary_color, secondary_color)
            VALUES ('Modular Course Platform', '#4a6cf7', '#6c757d')
            ''')
        
        # Check if the platform_config table has the email fields
        try:
            cursor.execute("SELECT smtp_server FROM platform_config LIMIT 1")
        except sqlite3.OperationalError:
            print("Adding email fields to platform_config table...")
            # Add the missing columns
            cursor.execute("ALTER TABLE platform_config ADD COLUMN smtp_server TEXT")
            cursor.execute("ALTER TABLE platform_config ADD COLUMN smtp_port INTEGER")
            cursor.execute("ALTER TABLE platform_config ADD COLUMN smtp_username TEXT")
            cursor.execute("ALTER TABLE platform_config ADD COLUMN smtp_password TEXT")
            cursor.execute("ALTER TABLE platform_config ADD COLUMN smtp_use_tls INTEGER DEFAULT 1")
            cursor.execute("ALTER TABLE platform_config ADD COLUMN smtp_use_ssl INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE platform_config ADD COLUMN smtp_default_sender TEXT")
            cursor.execute("ALTER TABLE platform_config ADD COLUMN smtp_enabled INTEGER DEFAULT 0")
        
        # Update the email configuration
        print("Updating email configuration...")
        cursor.execute("""
        UPDATE platform_config SET 
            smtp_server = ?,
            smtp_port = ?,
            smtp_username = ?,
            smtp_password = ?,
            smtp_use_tls = ?,
            smtp_use_ssl = ?,
            smtp_default_sender = ?,
            smtp_enabled = ?
        """, (
            CONFIG['smtp_server'],
            CONFIG['smtp_port'],
            CONFIG['smtp_username'],
            CONFIG['smtp_password'],
            CONFIG['smtp_use_tls'],
            CONFIG['smtp_use_ssl'],
            CONFIG['smtp_default_sender'],
            CONFIG['smtp_enabled']
        ))
        
        # Check if email_templates table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='email_templates'")
        if not cursor.fetchone():
            print("Creating email_templates table...")
            cursor.execute('''
            CREATE TABLE email_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                subject TEXT NOT NULL,
                body_html TEXT NOT NULL,
                body_text TEXT,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                template_key TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Insert default templates
            templates = [
                {
                    'name': 'User Registration Welcome',
                    'subject': 'Welcome to {{ config.platform_name }}',
                    'body_html': '''
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <h1>Welcome to {{ config.platform_name }}, {{ user.name }}!</h1>
                        <p>Thank you for registering with us. We're excited to have you on board.</p>
                        <p>Your account has been created and you can now access all our features.</p>
                        <p><a href="{{ login_url }}" style="display: inline-block; background-color: {{ config.primary_color }}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Login to your account</a></p>
                        <p>If you have any questions, please don't hesitate to contact us.</p>
                        <p>Best regards,<br>The {{ config.platform_name }} Team</p>
                    </div>
                    ''',
                    'body_text': '''
                    Welcome to {{ config.platform_name }}, {{ user.name }}!
                    
                    Thank you for registering with us. We're excited to have you on board.
                    Your account has been created and you can now access all our features.
                    
                    You can login to your account here: {{ login_url }}
                    
                    If you have any questions, please don't hesitate to contact us.
                    
                    Best regards,
                    The {{ config.platform_name }} Team
                    ''',
                    'description': 'Email sent to users when they register for an account',
                    'template_key': 'user_registration'
                },
                {
                    'name': 'Course Enrollment Confirmation',
                    'subject': 'You are now enrolled in {{ course.title }}',
                    'body_html': '''
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <h1>You're now enrolled in {{ course.title }}!</h1>
                        <p>Hello {{ user.name }},</p>
                        <p>We're excited to confirm your enrollment in <strong>{{ course.title }}</strong>.</p>
                        {% if course.is_free %}
                        <p>This is a free course, and you have full access to all materials.</p>
                        {% else %}
                        <p>Your payment of ${{ course.price }} has been successfully processed.</p>
                        {% endif %}
                        <p><a href="{{ course_url }}" style="display: inline-block; background-color: {{ config.primary_color }}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Start Learning Now</a></p>
                        <p>We hope you enjoy the course and learn a lot!</p>
                        <p>Best regards,<br>The {{ config.platform_name }} Team</p>
                    </div>
                    ''',
                    'body_text': '''
                    You're now enrolled in {{ course.title }}!
                    
                    Hello {{ user.name }},
                    
                    We're excited to confirm your enrollment in {{ course.title }}.
                    
                    {% if course.is_free %}
                    This is a free course, and you have full access to all materials.
                    {% else %}
                    Your payment of ${{ course.price }} has been successfully processed.
                    {% endif %}
                    
                    You can start learning now at: {{ course_url }}
                    
                    We hope you enjoy the course and learn a lot!
                    
                    Best regards,
                    The {{ config.platform_name }} Team
                    ''',
                    'description': 'Email sent to users when they enroll in a course',
                    'template_key': 'course_enrollment'
                },
                {
                    'name': 'Course Completion Congratulations',
                    'subject': 'Congratulations on completing {{ course.title }}!',
                    'body_html': '''
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <h1>Congratulations, {{ user.name }}!</h1>
                        <p>You have successfully completed <strong>{{ course.title }}</strong>. This is a significant achievement that demonstrates your dedication to learning.</p>
                        {% if course.has_certificate %}
                        <p>Your certificate of completion is ready to download.</p>
                        <p><a href="{{ certificate_url }}" style="display: inline-block; background-color: {{ config.primary_color }}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Download Your Certificate</a></p>
                        {% endif %}
                        <p>We hope you found the course valuable and enriching. Keep up the great work!</p>
                        <p>Best regards,<br>The {{ config.platform_name }} Team</p>
                    </div>
                    ''',
                    'body_text': '''
                    Congratulations, {{ user.name }}!
                    
                    You have successfully completed {{ course.title }}. This is a significant achievement that demonstrates your dedication to learning.
                    
                    {% if course.has_certificate %}
                    Your certificate of completion is ready to download.
                    
                    Download your certificate here: {{ certificate_url }}
                    {% endif %}
                    
                    We hope you found the course valuable and enriching. Keep up the great work!
                    
                    Best regards,
                    The {{ config.platform_name }} Team
                    ''',
                    'description': 'Email sent to users when they complete a course',
                    'template_key': 'course_completion'
                },
                {
                    'name': 'Quiz Completion Results',
                    'subject': 'Your quiz results for {{ quiz.title }}',
                    'body_html': '''
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <h1>Your Quiz Results</h1>
                        <p>Hello {{ user.name }},</p>
                        <p>You have completed the quiz for <strong>{{ quiz.title }}</strong>.</p>
                        <div style="border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 5px; text-align: center;">
                            <h2 style="margin-top: 0;">Your Score: {{ quiz_attempt.score }}%</h2>
                            <p style="font-size: 18px; margin-bottom: 0;">
                                {% if quiz_attempt.passed %}
                                <span style="color: green;">✓ Passed</span>
                                {% else %}
                                <span style="color: red;">✗ Not Passed</span>
                                {% endif %}
                            </p>
                        </div>
                        <p>
                            {% if quiz_attempt.passed %}
                            Congratulations on passing the quiz! You can now continue with the rest of the course.
                            {% else %}
                            Don't worry if you didn't pass this time. You can review the material and try again.
                            {% endif %}
                        </p>
                        <p><a href="{{ quiz_results_url }}" style="display: inline-block; background-color: {{ config.primary_color }}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Detailed Results</a></p>
                        <p>Best regards,<br>The {{ config.platform_name }} Team</p>
                    </div>
                    ''',
                    'body_text': '''
                    Your Quiz Results
                    
                    Hello {{ user.name }},
                    
                    You have completed the quiz for {{ quiz.title }}.
                    
                    Your Score: {{ quiz_attempt.score }}%
                    
                    {% if quiz_attempt.passed %}
                    Congratulations on passing the quiz! You can now continue with the rest of the course.
                    {% else %}
                    Don't worry if you didn't pass this time. You can review the material and try again.
                    {% endif %}
                    
                    View detailed results here: {{ quiz_results_url }}
                    
                    Best regards,
                    The {{ config.platform_name }} Team
                    ''',
                    'description': 'Email sent to users with their quiz results',
                    'template_key': 'quiz_completion'
                },
                {
                    'name': 'Product Purchase Confirmation',
                    'subject': 'Your purchase of {{ product.title }} - Order Confirmation',
                    'body_html': '''
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <h1>Thank you for your purchase!</h1>
                        <p>Hello {{ user.name }},</p>
                        <p>Your purchase of <strong>{{ product.title }}</strong> has been successfully processed.</p>
                        <div style="border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 5px;">
                            <h3 style="margin-top: 0;">Order Details</h3>
                            <p><strong>Product:</strong> {{ product.title }}</p>
                            <p><strong>Price:</strong> ${{ product.price }}</p>
                            <p><strong>Order Date:</strong> {{ purchase.purchase_date|date }}</p>
                            <p><strong>Order ID:</strong> {{ purchase.id }}</p>
                        </div>
                        {% if product.download_link %}
                        <p>You can download your purchase using the link below:</p>
                        <p><a href="{{ download_url }}" style="display: inline-block; background-color: {{ config.primary_color }}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Download Your Product</a></p>
                        {% endif %}
                        {% if product.external_url %}
                        <p>You can access your product here:</p>
                        <p><a href="{{ product.external_url }}" style="display: inline-block; background-color: {{ config.primary_color }}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Access Your Product</a></p>
                        {% endif %}
                        <p>If you have any questions or need assistance, please don't hesitate to contact us.</p>
                        <p>Best regards,<br>The {{ config.platform_name }} Team</p>
                    </div>
                    ''',
                    'body_text': '''
                    Thank you for your purchase!
                    
                    Hello {{ user.name }},
                    
                    Your purchase of {{ product.title }} has been successfully processed.
                    
                    Order Details:
                    Product: {{ product.title }}
                    Price: ${{ product.price }}
                    Order Date: {{ purchase.purchase_date|date }}
                    Order ID: {{ purchase.id }}
                    
                    {% if product.download_link %}
                    You can download your purchase using this link: {{ download_url }}
                    {% endif %}
                    
                    {% if product.external_url %}
                    You can access your product here: {{ product.external_url }}
                    {% endif %}
                    
                    If you have any questions or need assistance, please don't hesitate to contact us.
                    
                    Best regards,
                    The {{ config.platform_name }} Team
                    ''',
                    'description': 'Email sent to users when they purchase a product',
                    'template_key': 'product_purchase'
                }
            ]
            
            for template in templates:
                cursor.execute('''
                INSERT INTO email_templates 
                    (name, subject, body_html, body_text, description, is_active, template_key) 
                VALUES 
                    (?, ?, ?, ?, ?, 1, ?)
                ''', (
                    template['name'],
                    template['subject'],
                    template['body_html'],
                    template['body_text'],
                    template['description'],
                    template['template_key']
                ))
                print(f"Added template: {template['name']}")
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        print("\nEmail configuration completed successfully!")
        print(f"SMTP Server: {CONFIG['smtp_server']}")
        print(f"SMTP Port: {CONFIG['smtp_port']}")
        print(f"SMTP Username: {CONFIG['smtp_username']}")
        print(f"Default Sender: {CONFIG['smtp_default_sender']}")
        print(f"Email sending is now enabled in your platform.")
        
        return True
        
    except Exception as e:
        print(f"Error configuring email: {str(e)}")
        if 'conn' in locals() and conn:
            conn.close()
        return False

if __name__ == "__main__":
    configure_email()
"""
Create email tables in the MySQL database
"""
import os
import pymysql
import sys
from config import Config

# SQL statements to create the email-related tables and columns
SQL_STATEMENTS = [
    # Add email-related columns to platform_config table if they don't exist
    """
    SELECT COUNT(*) AS column_exists 
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'platform_config' AND COLUMN_NAME = 'smtp_server'
    """,
    
    """
    ALTER TABLE platform_config
    ADD COLUMN smtp_server VARCHAR(255) NULL,
    ADD COLUMN smtp_port INT NULL DEFAULT 587,
    ADD COLUMN smtp_username VARCHAR(255) NULL,
    ADD COLUMN smtp_password VARCHAR(255) NULL,
    ADD COLUMN smtp_use_tls TINYINT(1) NULL DEFAULT 1,
    ADD COLUMN smtp_use_ssl TINYINT(1) NULL DEFAULT 0,
    ADD COLUMN smtp_default_sender VARCHAR(255) NULL,
    ADD COLUMN smtp_enabled TINYINT(1) NULL DEFAULT 0
    """,
    
    # Create email_templates table
    """
    CREATE TABLE IF NOT EXISTS email_templates (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        subject VARCHAR(255) NOT NULL,
        body_html TEXT NOT NULL,
        body_text TEXT NULL,
        description TEXT NULL,
        is_active TINYINT(1) NOT NULL DEFAULT 1,
        template_key VARCHAR(255) NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """
]

# Default email templates to insert
EMAIL_TEMPLATES = [
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

# Email configuration values
EMAIL_CONFIG = {
    'smtp_server': 'smtp.mailgun.org',
    'smtp_port': 587,
    'smtp_username': 'example@mail.example.com',
    'smtp_password': 'your-mailgun-api-key-here',
    'smtp_use_tls': 1,
    'smtp_use_ssl': 0,
    'smtp_default_sender': 'example@mail.example.com',
    'smtp_enabled': 1
}

def create_email_tables():
    """Create the necessary email tables in the MySQL database"""
    try:
        # Connect to the database
        conn = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        
        cursor = conn.cursor()
        print(f"Connected to MySQL database: {Config.DB_HOST}:{Config.DB_PORT}")
        
        # Check if smtp columns already exist in platform_config
        cursor.execute(SQL_STATEMENTS[0], (Config.DB_NAME,))
        column_exists = cursor.fetchone()[0] > 0
        
        if not column_exists:
            print("Adding email columns to platform_config table...")
            cursor.execute(SQL_STATEMENTS[1])
            print("Email columns added successfully!")
        else:
            print("Email columns already exist in platform_config table.")
        
        # Create email_templates table
        print("Creating email_templates table if it doesn't exist...")
        cursor.execute(SQL_STATEMENTS[2])
        print("Email templates table created successfully!")
        
        # Set up default email configuration
        print("Configuring email settings...")
        cursor.execute("""
        UPDATE platform_config SET 
            smtp_server = %s,
            smtp_port = %s,
            smtp_username = %s,
            smtp_password = %s,
            smtp_use_tls = %s,
            smtp_use_ssl = %s,
            smtp_default_sender = %s,
            smtp_enabled = %s
        """, (
            EMAIL_CONFIG['smtp_server'],
            EMAIL_CONFIG['smtp_port'],
            EMAIL_CONFIG['smtp_username'],
            EMAIL_CONFIG['smtp_password'],
            EMAIL_CONFIG['smtp_use_tls'],
            EMAIL_CONFIG['smtp_use_ssl'],
            EMAIL_CONFIG['smtp_default_sender'],
            EMAIL_CONFIG['smtp_enabled']
        ))
        
        # Insert default email templates
        print("Inserting default email templates...")
        for template in EMAIL_TEMPLATES:
            # Check if template already exists
            cursor.execute("SELECT COUNT(*) FROM email_templates WHERE template_key = %s", (template['template_key'],))
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                INSERT INTO email_templates 
                    (name, subject, body_html, body_text, description, is_active, template_key) 
                VALUES 
                    (%s, %s, %s, %s, %s, 1, %s)
                """, (
                    template['name'],
                    template['subject'],
                    template['body_html'],
                    template['body_text'],
                    template['description'],
                    template['template_key']
                ))
                print(f"Added template: {template['name']}")
            else:
                print(f"Template {template['name']} already exists, skipping...")
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        print("\nEmail configuration completed successfully!")
        print(f"SMTP Server: {EMAIL_CONFIG['smtp_server']}")
        print(f"SMTP Port: {EMAIL_CONFIG['smtp_port']}")
        print(f"SMTP Username: {EMAIL_CONFIG['smtp_username']}")
        print(f"Default Sender: {EMAIL_CONFIG['smtp_default_sender']}")
        print(f"Email sending is now enabled in your platform.")
        
        return True
        
    except Exception as e:
        print(f"Error configuring email tables: {str(e)}")
        if 'conn' in locals() and conn:
            conn.close()
        return False

if __name__ == "__main__":
    create_email_tables()
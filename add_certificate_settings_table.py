"""
Migration script to add certificate_settings table to the database
"""
import os
import sys
import traceback
from flask import Flask
from sqlalchemy import text

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import after adding to path
try:
    from app import db, create_app
    print("Successfully imported app modules")
except Exception as e:
    print(f"Error importing app modules: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

try:
    # Create app with the database configuration
    print("Creating Flask app...")
    app = create_app()
    print("Flask app created successfully")
except Exception as e:
    print(f"Error creating Flask app: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

def add_certificate_settings_table():
    """Add certificate_settings table to the database"""
    print("Starting migration to add certificate_settings table...")
    
    try:
        with app.app_context():
            try:
                print("Connecting to database...")
                # Connect using SQLAlchemy engine
                connection = db.engine.connect()
                print("Database connection established")
                
                # Check if certificate_settings table exists
                print("Checking if certificate_settings table exists...")
                check_table = text("SHOW TABLES LIKE 'certificate_settings'")
                result = connection.execute(check_table)
                table_exists = result.fetchone() is not None
                
                # Create certificate_settings table if it doesn't exist
                if not table_exists:
                    print("Table does not exist, creating it now...")
                    create_table_query = text("""
                    CREATE TABLE certificate_settings (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        background_color VARCHAR(20) DEFAULT '#FFFFFF' NOT NULL,
                        border_color VARCHAR(20) DEFAULT '#294767' NOT NULL,
                        text_color VARCHAR(20) DEFAULT '#000000' NOT NULL,
                        signature_image VARCHAR(255),
                        logo_image VARCHAR(255),
                        certificate_title VARCHAR(255) DEFAULT 'CERTIFICATE OF COMPLETION' NOT NULL,
                        certificate_text TEXT DEFAULT 'has successfully completed the course',
                        footer_text TEXT DEFAULT '',
                        instructor_name VARCHAR(100) DEFAULT 'Course Instructor' NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                    """)
                    connection.execute(create_table_query)
                    print("Table created successfully")
                    
                    # Insert default record
                    print("Inserting default values...")
                    insert_default = text("""
                    INSERT INTO certificate_settings (
                        background_color, border_color, text_color, 
                        certificate_title, certificate_text, 
                        footer_text, instructor_name
                    ) VALUES (
                        '#FFFFFF', '#294767', '#000000', 
                        'CERTIFICATE OF COMPLETION', 'has successfully completed the course', 
                        '', 'Course Instructor'
                    )
                    """)
                    connection.execute(insert_default)
                    print("Default values inserted successfully")
                    
                    print("Committing changes...")
                    connection.commit()
                    print("Successfully created certificate_settings table with default values")
                else:
                    print("Certificate settings table already exists")
                    
                connection.close()
                print("Database migration completed successfully")
                return True
            except Exception as e:
                print(f"Database error: {str(e)}")
                traceback.print_exc()
                return False
    except Exception as e:
        print(f"App context error: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = add_certificate_settings_table()
    if success:
        print("Migration completed successfully!")
        sys.exit(0)
    else:
        print("Migration failed!")
        sys.exit(1)
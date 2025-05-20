"""
Migration script to add the certificate template table and relationship to courses
"""
import os
import sys
import pymysql
from config import Config

def migrate():
    """
    Add the certificate_templates table and certificate_template_id column to courses
    """
    print("Starting migration: Adding certificate templates table...")

    try:
        # Connect to the database
        connection = pymysql.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            port=Config.DB_PORT
        )

        with connection.cursor() as cursor:
            # Check if the certificate_templates table already exists
            cursor.execute("SHOW TABLES LIKE 'certificate_templates'")
            if cursor.fetchone():
                print("Certificate templates table already exists. Skipping creation.")
            else:
                # Create the certificate_templates table
                print("Creating certificate_templates table...")
                cursor.execute("""
                CREATE TABLE certificate_templates (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    background_color VARCHAR(20) DEFAULT '#FFFFFF',
                    border_color VARCHAR(20) DEFAULT '#294767',
                    text_color VARCHAR(20) DEFAULT '#000000',
                    signature_path VARCHAR(255),
                    logo_path VARCHAR(255),
                    certificate_title VARCHAR(255) DEFAULT 'CERTIFICATE OF COMPLETION',
                    certificate_text TEXT DEFAULT 'has successfully completed the course',
                    footer_text TEXT DEFAULT '',
                    instructor_name VARCHAR(100) DEFAULT 'Course Instructor',
                    font VARCHAR(100) DEFAULT 'Arial, sans-serif',
                    is_default BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
                """)
                print("Certificate templates table created successfully")

                # Create a default template
                cursor.execute("""
                INSERT INTO certificate_templates (
                    name, description, is_default
                ) VALUES (
                    'Default Certificate', 'Default certificate template for all courses', TRUE
                )
                """)
                print("Default certificate template created successfully")

            # Check if the certificate_template_id column exists in the courses table
            cursor.execute("SHOW COLUMNS FROM courses LIKE 'certificate_template_id'")
            if cursor.fetchone():
                print("certificate_template_id column already exists in courses table. Skipping addition.")
            else:
                # Add the certificate_template_id column to the courses table
                print("Adding certificate_template_id column to courses table...")
                cursor.execute("""
                ALTER TABLE courses 
                ADD COLUMN certificate_template_id INT,
                ADD CONSTRAINT fk_certificate_template
                FOREIGN KEY (certificate_template_id) REFERENCES certificate_templates(id)
                """)
                print("certificate_template_id column added successfully")

                # Set default certificate template for courses that have certificates enabled
                print("Setting default certificate template for courses with certificates...")
                cursor.execute("""
                UPDATE courses SET certificate_template_id = (
                    SELECT id FROM certificate_templates WHERE is_default = TRUE LIMIT 1
                ) WHERE has_certificate = TRUE
                """)

            connection.commit()
            print("Migration completed successfully!")
            return True

    except Exception as e:
        print(f"Migration failed: {str(e)}")
        return False
    finally:
        if 'connection' in locals() and connection:
            connection.close()

if __name__ == "__main__":
    # Allow the script to be run from anywhere
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("=================================================")
    print("  Certificate Templates Database Migration Tool")
    print("=================================================")
    
    success = migrate()
    
    if success:
        print("Certificate templates migration completed successfully!")
        sys.exit(0)
    else:
        print("Certificate templates migration failed!")
        sys.exit(1)
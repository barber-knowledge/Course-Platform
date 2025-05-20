"""
Add bio column to users table.

This script adds the missing column needed for user biographical information.
Uses direct database connection instead of Flask-SQLAlchemy.
"""

import pymysql
from config import Config

def add_column():
    """Add bio column to users table"""
    
    # Create database connection using parameters from config
    connection = pymysql.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        port=Config.DB_PORT
    )
    
    try:
        with connection.cursor() as cursor:
            # Check if column exists
            cursor.execute("SHOW COLUMNS FROM users LIKE 'bio'")
            bio_exists = cursor.fetchone() is not None
            
            # Add bio column if it doesn't exist
            if not bio_exists:
                print("Adding bio column to users table...")
                cursor.execute('ALTER TABLE users ADD COLUMN bio TEXT NULL')
                print("Column bio added successfully.")
            else:
                print("Column bio already exists.")
                
            # Commit the changes
            connection.commit()
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        connection.close()

if __name__ == '__main__':
    # Run the migration
    print("Starting migration to add bio column...")
    add_column()
    print("Migration completed.")
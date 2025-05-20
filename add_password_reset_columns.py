"""
Add reset_password_token and reset_token_expires_at columns to users table.

This script adds the missing columns needed for password reset functionality.
Uses direct database connection instead of Flask-SQLAlchemy.
"""

import pymysql
from config import Config

def add_columns():
    """Add reset_password_token and reset_token_expires_at columns to users table"""
    
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
            # Check if columns exist
            cursor.execute("SHOW COLUMNS FROM users LIKE 'reset_password_token'")
            reset_token_exists = cursor.fetchone() is not None
            
            cursor.execute("SHOW COLUMNS FROM users LIKE 'reset_token_expires_at'")
            expires_at_exists = cursor.fetchone() is not None
            
            # Add reset_password_token column if it doesn't exist
            if not reset_token_exists:
                print("Adding reset_password_token column to users table...")
                cursor.execute('ALTER TABLE users ADD COLUMN reset_password_token VARCHAR(100) NULL')
                print("Column reset_password_token added successfully.")
            else:
                print("Column reset_password_token already exists.")
                
            # Add reset_token_expires_at column if it doesn't exist
            if not expires_at_exists:
                print("Adding reset_token_expires_at column to users table...")
                cursor.execute('ALTER TABLE users ADD COLUMN reset_token_expires_at DATETIME NULL')
                print("Column reset_token_expires_at added successfully.")
            else:
                print("Column reset_token_expires_at already exists.")
                
            # Commit the changes
            connection.commit()
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        connection.close()

if __name__ == '__main__':
    # Run the migration
    print("Starting migration to add password reset columns...")
    add_columns()
    print("Migration completed.")
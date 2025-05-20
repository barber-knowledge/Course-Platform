"""
Add last_login column to users table.

This script adds the missing column needed for tracking user login times.
Uses direct database connection instead of Flask-SQLAlchemy.
"""

import pymysql
from config import Config

def add_column():
    """Add last_login column to users table"""
    
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
            cursor.execute("SHOW COLUMNS FROM users LIKE 'last_login'")
            last_login_exists = cursor.fetchone() is not None
            
            # Add last_login column if it doesn't exist
            if not last_login_exists:
                print("Adding last_login column to users table...")
                cursor.execute('ALTER TABLE users ADD COLUMN last_login DATETIME NULL')
                print("Column last_login added successfully.")
            else:
                print("Column last_login already exists.")
                
            # Commit the changes
            connection.commit()
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        connection.close()

if __name__ == '__main__':
    # Run the migration
    print("Starting migration to add last_login column...")
    add_column()
    print("Migration completed.")
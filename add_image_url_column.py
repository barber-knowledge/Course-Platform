"""
Migration script to add image_url column to courses table
"""
import os
import sys
from flask import Flask
from sqlalchemy import text

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import after adding to path
from app import db, create_app

# Create app with the database configuration
app = create_app()

def add_image_url_column():
    """Add image_url column to courses table"""
    with app.app_context():
        try:
            # Connect using SQLAlchemy engine
            connection = db.engine.connect()
            
            # Check if column already exists to avoid errors
            check_query = text("SHOW COLUMNS FROM courses LIKE 'image_url'")
            result = connection.execute(check_query)
            column_exists = result.fetchone() is not None
            
            if not column_exists:
                # Execute ALTER TABLE statement
                alter_query = text("ALTER TABLE courses ADD COLUMN image_url VARCHAR(255) NULL")
                connection.execute(alter_query)
                connection.commit()
                print("Successfully added image_url column to courses table")
            else:
                print("Column image_url already exists in courses table")
                
            connection.close()
            return True
        except Exception as e:
            print(f"Error adding column: {str(e)}")
            return False

if __name__ == "__main__":
    add_image_url_column()
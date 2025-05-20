"""
Migration script to add additional marketing fields to the Course model
to enhance the course landing pages with more information.
"""
import sys
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Text, String, Boolean

# Set the path to include the parent directory
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import config
from config import Config

# Create a minimal Flask application
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

def migrate():
    """Add marketing fields to Course table"""
    with app.app_context():
        # Get database connection and create a cursor
        conn = db.engine.connect()
        
        # Add the new columns
        print("Adding new marketing fields to Course table...")
        
        # Adding testimonials column
        conn.execute("ALTER TABLE courses ADD COLUMN testimonials TEXT")
        print("Added testimonials column")
        
        # Adding features column
        conn.execute("ALTER TABLE courses ADD COLUMN features TEXT")
        print("Added features column")
        
        # Adding is_featured column
        conn.execute("ALTER TABLE courses ADD COLUMN is_featured BOOLEAN DEFAULT FALSE")
        print("Added is_featured column")
        
        # Adding gallery_images column
        conn.execute("ALTER TABLE courses ADD COLUMN gallery_images TEXT")
        print("Added gallery_images column")
        
        # Adding related_courses column
        conn.execute("ALTER TABLE courses ADD COLUMN related_courses TEXT")
        print("Added related_courses column")
        
        # Adding pricing_tiers column
        conn.execute("ALTER TABLE courses ADD COLUMN pricing_tiers TEXT")
        print("Added pricing_tiers column")
        
        # Adding CTA buttons text
        conn.execute("ALTER TABLE courses ADD COLUMN cta_primary_text VARCHAR(100) DEFAULT 'Enroll Now'")
        print("Added cta_primary_text column")
        
        conn.execute("ALTER TABLE courses ADD COLUMN cta_secondary_text VARCHAR(100) DEFAULT 'Learn More'")
        print("Added cta_secondary_text column")
        
        # Adding SEO keywords
        conn.execute("ALTER TABLE courses ADD COLUMN seo_keywords TEXT")
        print("Added seo_keywords column")
        
        # Commit the transaction
        conn.close()
        print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
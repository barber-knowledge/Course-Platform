"""
Add additional marketing and user information fields to Product and Course models
"""
import sys
import os

# Add the parent directory to the path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import db
from app.models import Product, Course
from sqlalchemy import Column, Text, String, Boolean, Float

def migrate():
    """Add additional fields to Product and Course models"""
    print("Starting migration to add additional fields to Product and Course models...")
    
    # Check if the database is accessible
    try:
        Product.query.first()
        Course.query.first()
        print("Database connection successful.")
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return
    
    # Add new columns to the products table
    with db.engine.connect() as conn:
        # Product model additions
        conn.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS testimonials TEXT")
        conn.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS features TEXT")
        conn.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS technical_specs TEXT")
        conn.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT FALSE")
        conn.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS gallery_images TEXT")
        conn.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS related_products TEXT")
        conn.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS download_link TEXT")
        conn.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS pricing_tiers TEXT")
        conn.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS cta_primary_text VARCHAR(100) DEFAULT 'Buy Now'")
        conn.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS cta_secondary_text VARCHAR(100) DEFAULT 'Learn More'")
        conn.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS seo_keywords TEXT")
        
        # Course model additions
        conn.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT FALSE")
        conn.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS testimonials TEXT")
        conn.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS instructors TEXT")
        conn.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS prerequisites TEXT")
        conn.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS course_length VARCHAR(100)")
        conn.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS difficulty_level VARCHAR(50)")
        conn.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS target_audience TEXT")
        conn.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS cta_primary_text VARCHAR(100) DEFAULT 'Enroll Now'")
        conn.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS cta_secondary_text VARCHAR(100) DEFAULT 'Learn More'")
        conn.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS related_courses TEXT")
        conn.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS seo_keywords TEXT")
        
        print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
"""
Migration script to add additional marketing fields to the Product model
to enhance the product landing pages with more information.
"""
import sys
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Text, String, Boolean, text

# Set the path to include the parent directory
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import config
from config import Config

# Create a minimal Flask application
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

def migrate():
    """Add marketing fields to Product table"""
    with app.app_context():
        # Get database connection and create a cursor
        conn = db.engine.connect()
        
        # Add the new columns
        print("Adding new marketing fields to Product table...")
        
        try:
            # Adding USP (Unique Selling Proposition) column
            conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS usp TEXT"))
            print("Added usp column")
            
            # Adding customer_avatars column (target customer profiles)
            conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS customer_avatars TEXT"))
            print("Added customer_avatars column")
            
            # Adding before_after column (customer transformation stories)
            conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS before_after TEXT"))
            print("Added before_after column")
            
            # Adding guarantee_text column
            conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS guarantee_text TEXT"))
            print("Added guarantee_text column")
            
            # Adding product_comparison column
            conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS product_comparison TEXT"))
            print("Added product_comparison column")
            
            # Adding limited_offer column
            conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS limited_offer TEXT"))
            print("Added limited_offer column")
            
            # Adding social_proof column
            conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS social_proof TEXT"))
            print("Added social_proof column")
            
            # Adding author_bio column
            conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS author_bio TEXT"))
            print("Added author_bio column")
            
            # Adding additional fields that might be missing from earlier migrations
            conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS testimonials TEXT"))
            print("Added testimonials column")
            
            conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS features TEXT"))
            print("Added features column")
            
            conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS technical_specs TEXT"))
            print("Added technical_specs column")
            
            conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT FALSE"))
            print("Added is_featured column")
            
            conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS gallery_images TEXT"))
            print("Added gallery_images column")
            
            conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS related_products TEXT"))
            print("Added related_products column")
            
            conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS download_link TEXT"))
            print("Added download_link column")
            
            conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS pricing_tiers TEXT"))
            print("Added pricing_tiers column")
            
            conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS cta_primary_text VARCHAR(100) DEFAULT 'Buy Now'"))
            print("Added cta_primary_text column")
            
            conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS cta_secondary_text VARCHAR(100) DEFAULT 'Learn More'"))
            print("Added cta_secondary_text column")
            
            conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS seo_keywords TEXT"))
            print("Added seo_keywords column")
            
            # Commit the transaction
            db.session.commit()
            print("Migration completed successfully.")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            db.session.rollback()
        finally:
            conn.close()

if __name__ == "__main__":
    migrate()
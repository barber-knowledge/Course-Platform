"""
Add landing page columns to courses and products tables
"""
import sys
from app import create_app, db
from sqlalchemy import text, inspect

def column_exists(table_name, column_name):
    """Check if column exists in table."""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def migrate_courses_table():
    """Adds landing page columns to the courses table."""
    try:
        print("Adding landing page columns to courses table...")
        
        # Define columns to add with their definitions
        columns_to_add = {
            "slug": "VARCHAR(255) NULL UNIQUE",
            "meta_title": "VARCHAR(255) NULL",
            "meta_description": "TEXT NULL",
            "benefits": "TEXT NULL",
            "faq": "TEXT NULL",
            "banner_text": "TEXT NULL",
            "banner_image": "VARCHAR(255) NULL",
            "detailed_description": "TEXT NULL",
            "promo_video_url": "VARCHAR(255) NULL"
        }
        
        # SQL for adding columns to courses table
        for column, definition in columns_to_add.items():
            if not column_exists('courses', column):
                print(f"Adding column '{column}' to courses table...")
                db.session.execute(text(f"ALTER TABLE courses ADD COLUMN {column} {definition}"))
            else:
                print(f"Column '{column}' already exists in courses table. Skipping...")
        
        # Add index for slug if it doesn't already exist
        inspector = inspect(db.engine)
        indexes = inspector.get_indexes('courses')
        index_names = [idx['name'] for idx in indexes]
        
        if 'ix_courses_slug' not in index_names and column_exists('courses', 'slug'):
            print("Creating index for slug column in courses table...")
            db.session.execute(text("CREATE INDEX ix_courses_slug ON courses (slug)"))
        
        db.session.commit()
        print("[SUCCESS] Landing page columns added to courses table")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to add landing page columns to courses table: {str(e)}")
        db.session.rollback()
        return False

def migrate_products_table():
    """Adds landing page columns to the products table."""
    try:
        print("Adding landing page columns to products table...")
        
        # Define columns to add with their definitions
        columns_to_add = {
            "slug": "VARCHAR(255) NULL UNIQUE",
            "meta_title": "VARCHAR(255) NULL",
            "meta_description": "TEXT NULL",
            "benefits": "TEXT NULL",
            "faq": "TEXT NULL",
            "banner_text": "TEXT NULL",
            "banner_image": "VARCHAR(255) NULL",
            "detailed_description": "TEXT NULL",
            "promo_video_url": "VARCHAR(255) NULL"
        }
        
        # SQL for adding columns to products table
        for column, definition in columns_to_add.items():
            if not column_exists('products', column):
                print(f"Adding column '{column}' to products table...")
                db.session.execute(text(f"ALTER TABLE products ADD COLUMN {column} {definition}"))
            else:
                print(f"Column '{column}' already exists in products table. Skipping...")
        
        # Add index for slug if it doesn't already exist
        inspector = inspect(db.engine)
        indexes = inspector.get_indexes('products')
        index_names = [idx['name'] for idx in indexes]
        
        if 'ix_products_slug' not in index_names and column_exists('products', 'slug'):
            print("Creating index for slug column in products table...")
            db.session.execute(text("CREATE INDEX ix_products_slug ON products (slug)"))
        
        db.session.commit()
        print("[SUCCESS] Landing page columns added to products table")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to add landing page columns to products table: {str(e)}")
        db.session.rollback()
        return False

def main():
    """Main migration function."""
    app = create_app()
    with app.app_context():
        print("Starting migration to add landing page columns...")
        
        courses_success = migrate_courses_table()
        products_success = migrate_products_table()
        
        if courses_success and products_success:
            print("[SUCCESS] Migration completed successfully!")
            return 0
        else:
            print("[ERROR] Migration failed. Check the logs for more details.")
            return 1

if __name__ == "__main__":
    sys.exit(main())
"""
Migration script to add products, popups, and popup_id column to videos table
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

def run_database_migration():
    """Add missing tables and columns to the database"""
    with app.app_context():
        try:
            # Connect using SQLAlchemy engine
            connection = db.engine.connect()
            
            # Step 1: Check if products table exists
            check_products = text("SHOW TABLES LIKE 'products'")
            result = connection.execute(check_products)
            products_exists = result.fetchone() is not None
            
            # Create products table if it doesn't exist
            if not products_exists:
                products_query = text("""
                CREATE TABLE products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
                    image_path VARCHAR(255),
                    external_url VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
                connection.execute(products_query)
                connection.commit()
                print("Successfully created products table")
            else:
                print("Products table already exists")
                
            # Step 2: Check if popups table exists
            check_popups = text("SHOW TABLES LIKE 'popups'")
            result = connection.execute(check_popups)
            popups_exists = result.fetchone() is not None
            
            # Create popups table if it doesn't exist
            if not popups_exists:
                popups_query = text("""
                CREATE TABLE popups (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    product_id INT NOT NULL,
                    popup_image VARCHAR(255),
                    popup_text TEXT,
                    popup_button_label VARCHAR(100) DEFAULT 'Learn More',
                    popup_trigger_seconds INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
                connection.execute(popups_query)
                connection.commit()
                print("Successfully created popups table")
            else:
                print("Popups table already exists")
                
            # Step 3: Check if is_free column exists in videos table
            check_is_free = text("SHOW COLUMNS FROM videos LIKE 'is_free'")
            result = connection.execute(check_is_free)
            is_free_exists = result.fetchone() is not None
            
            # Add is_free column if it doesn't exist
            if not is_free_exists:
                alter_is_free = text("ALTER TABLE videos ADD COLUMN is_free BOOLEAN DEFAULT FALSE")
                connection.execute(alter_is_free)
                connection.commit()
                print("Successfully added is_free column to videos table")
            else:
                print("Column is_free already exists in videos table")
                
            # Step 4: Check if popup_id column exists in videos table
            check_popup_id = text("SHOW COLUMNS FROM videos LIKE 'popup_id'")
            result = connection.execute(check_popup_id)
            popup_id_exists = result.fetchone() is not None
            
            # Add popup_id column if it doesn't exist
            if not popup_id_exists:
                alter_popup_id = text("ALTER TABLE videos ADD COLUMN popup_id INT NULL")
                connection.execute(alter_popup_id)
                
                # Add foreign key constraint separately (to handle case where table exists but constraint doesn't)
                try:
                    add_fk = text("ALTER TABLE videos ADD CONSTRAINT fk_videos_popup FOREIGN KEY (popup_id) REFERENCES popups(id) ON DELETE SET NULL")
                    connection.execute(add_fk)
                    connection.commit()
                    print("Successfully added popup_id column with foreign key constraint to videos table")
                except Exception as e:
                    print(f"Foreign key constraint creation failed: {str(e)}")
                    print("Added popup_id column but could not add foreign key constraint")
            else:
                print("Column popup_id already exists in videos table")
                
            connection.close()
            print("Database migration completed successfully")
            return True
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            return False

if __name__ == "__main__":
    run_database_migration()
"""
Migration script to add product_purchases table to the database
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
    """Add product_purchases table to the database"""
    with app.app_context():
        try:
            # Connect using SQLAlchemy engine
            connection = db.engine.connect()
            
            # Check if product_purchases table already exists
            check_table = text("SHOW TABLES LIKE 'product_purchases'")
            result = connection.execute(check_table)
            table_exists = result.fetchone() is not None
            
            if not table_exists:
                # Create product_purchases table if it doesn't exist
                create_table_query = text("""
                CREATE TABLE product_purchases (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    product_id INT NOT NULL,
                    stripe_payment_id VARCHAR(100) UNIQUE,
                    amount DECIMAL(10, 2) NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'completed',
                    purchase_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                    UNIQUE KEY _user_product_purchase_uc (user_id, product_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
                connection.execute(create_table_query)
                connection.commit()
                print("Successfully created product_purchases table")
            else:
                print("product_purchases table already exists")
                
            connection.close()
            print("Database migration for product purchases completed successfully")
            return True
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            return False

if __name__ == "__main__":
    run_database_migration()
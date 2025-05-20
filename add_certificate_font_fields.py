import os
import pymysql
from config import Config

def add_certificate_font_fields():
    """Add font, auto_issue, and send_email columns to certificate_settings table"""
    try:
        # Connect to MySQL database using config settings
        conn = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = conn.cursor()
        
        print(f"Connected to MySQL database at {Config.DB_HOST}")
        
        # Check if table exists
        cursor.execute("SHOW TABLES LIKE 'certificate_settings'")
        if not cursor.fetchone():
            print("Error: certificate_settings table does not exist")
            conn.close()
            return
        
        # Check if columns exist
        cursor.execute("DESCRIBE certificate_settings")
        columns = [col[0] for col in cursor.fetchall()]
        
        # Add font column if it doesn't exist
        if 'font' not in columns:
            cursor.execute("ALTER TABLE certificate_settings ADD COLUMN font VARCHAR(100) DEFAULT 'Arial, sans-serif'")
            print("Added 'font' column to certificate_settings table")
            
        # Add auto_issue column if it doesn't exist
        if 'auto_issue' not in columns:
            cursor.execute("ALTER TABLE certificate_settings ADD COLUMN auto_issue BOOLEAN DEFAULT 1")
            print("Added 'auto_issue' column to certificate_settings table")
            
        # Add send_email column if it doesn't exist
        if 'send_email' not in columns:
            cursor.execute("ALTER TABLE certificate_settings ADD COLUMN send_email BOOLEAN DEFAULT 1")
            print("Added 'send_email' column to certificate_settings table")
            
        conn.commit()
        print("Migration completed successfully")
        
    except pymysql.Error as e:
        print(f"Database error: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    add_certificate_font_fields()
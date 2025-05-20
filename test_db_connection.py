"""
Database connection tester for Modular Course Platform

This script tests the connection to the MariaDB database server
and verifies that the database exists and is accessible.
"""
import pymysql
import sys
from config import Config

def test_database_connection():
    """Test the connection to the MariaDB database"""
    print(f"Testing connection to {Config.DB_HOST}:{Config.DB_PORT}...")
    
    try:
        # Connect to MariaDB with the credentials from Config
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            charset='utf8mb4'
        )
        
        print("[SUCCESS] Successfully connected to database server!")
        
        with connection.cursor() as cursor:
            # Check if database exists
            cursor.execute(f"SHOW DATABASES LIKE '{Config.DB_NAME}';")
            result = cursor.fetchone()
            
            if not result:
                print(f"[ERROR] Database '{Config.DB_NAME}' doesn't exist.")
                return False
            else:
                print(f"[SUCCESS] Database '{Config.DB_NAME}' exists.")
                
            # Try to use the database
            cursor.execute(f"USE {Config.DB_NAME};")
            print(f"[SUCCESS] Successfully accessed database '{Config.DB_NAME}'.")
            
            # Check if we can create and drop a test table
            try:
                cursor.execute("CREATE TABLE test_connection (id INT);")
                cursor.execute("DROP TABLE test_connection;")
                print("[SUCCESS] Successfully created and dropped a test table.")
            except Exception as e:
                print(f"[ERROR] Could not create/drop table: {str(e)}")
                return False
        
        connection.close()
        return True
    except Exception as e:
        print(f"[ERROR] Error connecting to database: {str(e)}")
        return False

if __name__ == "__main__":
    print("==========================================")
    print("  MariaDB Connection Test")
    print("==========================================")
    print(f"Host:     {Config.DB_HOST}")
    print(f"Port:     {Config.DB_PORT}")
    print(f"Database: {Config.DB_NAME}")
    print(f"User:     {Config.DB_USER}")
    print("------------------------------------------")
    
    success = test_database_connection()
    
    print("==========================================")
    if success:
        print("[SUCCESS] All tests passed! Database connection is working correctly.")
        sys.exit(0)
    else:
        print("[ERROR] Connection test failed. Please check your database settings.")
        sys.exit(1)
"""
Add RabbitMQ columns to platform_config table
"""
from flask import Flask
from app import db, create_app
from app.models import PlatformConfig
from sqlalchemy import text

print("Adding RabbitMQ columns to platform_config table...")

app = create_app()
with app.app_context():
    # Add the columns if they don't exist using SQLAlchemy's text() for raw SQL
    try:
        # Use raw SQL with text() to check if columns exist
        with db.engine.connect() as conn:
            # Check if rabbitmq_host exists
            result = conn.execute(text("SHOW COLUMNS FROM platform_config LIKE 'rabbitmq_host'"))
            exists = result.fetchone() is not None
            
            if not exists:
                # Add rabbitmq columns
                conn.execute(text("ALTER TABLE platform_config ADD COLUMN rabbitmq_host VARCHAR(255) DEFAULT 'localhost'"))
                conn.execute(text("ALTER TABLE platform_config ADD COLUMN rabbitmq_port INT DEFAULT 5672"))
                conn.execute(text("ALTER TABLE platform_config ADD COLUMN rabbitmq_username VARCHAR(255) DEFAULT 'guest'"))
                conn.execute(text("ALTER TABLE platform_config ADD COLUMN rabbitmq_password VARCHAR(255) DEFAULT 'guest'"))
                conn.execute(text("ALTER TABLE platform_config ADD COLUMN rabbitmq_vhost VARCHAR(255) DEFAULT '/'"))
                conn.execute(text("ALTER TABLE platform_config ADD COLUMN rabbitmq_enabled BOOLEAN DEFAULT 0"))
                conn.commit()
                
                print("RabbitMQ columns added successfully!")
            else:
                print("RabbitMQ columns already exist.")
            
    except Exception as e:
        print(f"Error adding RabbitMQ columns: {e}")
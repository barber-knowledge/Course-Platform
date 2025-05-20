from app import create_app, db
from app.models import CertificateSettings

app = create_app()

print("Starting migration: Adding certificate_text_template column...")

with app.app_context():
    try:
        # Execute raw SQL to add the missing column
        db.session.execute(db.text('ALTER TABLE certificate_settings ADD COLUMN certificate_text_template TEXT NULL;'))
        db.session.commit()
        print("Column 'certificate_text_template' successfully added to certificate_settings table.")
    except Exception as e:
        db.session.rollback()
        print(f"Error adding column: {str(e)}")
        # Check if error is because column already exists
        if "Duplicate column" in str(e) or "already exists" in str(e):
            print("Column already exists, no changes needed.")
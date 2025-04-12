from app import create_app, db
from app.models import PlatformConfig

app = create_app()

with app.app_context():
    # Reset or create platform config
    config = PlatformConfig.query.first()
    if config:
        config.setup_complete = False
        db.session.commit()
        print("Setup status reset successfully!")
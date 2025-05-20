from flask import Blueprint

bp = Blueprint('payments', __name__, url_prefix='/payments')

from app.blueprints.payments import routes
from app.blueprints.payments.webhook import webhook_bp
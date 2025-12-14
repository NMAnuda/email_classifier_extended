from flask import Flask
from flask_socketio import SocketIO, emit
from app.routers import email_router
from flask_cors import CORS
from app.services.gmail_service import enable_watch
import os
from functools import lru_cache  # New: For lazy model load

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')
cors_origins = os.getenv('FLASK_CORS_ORIGINS', 'http://localhost:3000')
CORS(app, origins=cors_origins)
socketio = SocketIO(app, cors_allowed_origins=cors_origins)

app.register_blueprint(email_router.bp)

# Enable watch
enable_watch()

# Lazy load classifier (init on first call, cache for reuse)
@lru_cache(maxsize=1)
def get_classifier():
    from app.services.classifier import classifier
    return classifier

# Update router calls to use get_classifier() instead of clf_module.classifier
# (In email_router.py, replace clf_module.classifier with get_classifier())

if __name__ == '__main__':
    socketio.run(app, debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true', host='0.0.0.0', port=int(os.getenv('PORT', 8000)), workers=1)  # Fixed: 1 worker for RAM
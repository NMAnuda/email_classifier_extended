import os
from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from app.routers import email_router
from app.services.gmail_service import enable_watch

# Disable TensorFlow warnings (optional)
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# CORS
cors_origins = os.getenv('FLASK_CORS_ORIGINS', 'http://localhost:3000')
CORS(app, origins=cors_origins)

# SocketIO
socketio = SocketIO(app, cors_allowed_origins=cors_origins)

# Register routes
app.register_blueprint(email_router.bp)

# Enable Gmail watch (if needed)
enable_watch()

if __name__ == '__main__':
    socketio.run(
        app,
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
        host='0.0.0.0',
        port=int(os.getenv('PORT', 8000))
    )

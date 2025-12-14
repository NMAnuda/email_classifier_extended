from flask import Flask
from flask_socketio import SocketIO, emit  # For SocketIO
from app.routers import email_router
from flask_cors import CORS
from app.services.gmail_service import enable_watch
import os

# Disable TensorFlow warnings (for Transformers)
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')  # Fixed: Env for security

# CORS: Specific origins (env for prod, localhost for dev)
cors_origins = os.getenv('FLASK_CORS_ORIGINS', 'http://localhost:3000')
CORS(app, origins=cors_origins)

# SocketIO: Specific origins (secure—no "*")
socketio = SocketIO(app, cors_allowed_origins=cors_origins)  # Matches CORS

app.register_blueprint(email_router.bp)

# Enable Gmail watch
enable_watch()

if __name__ == '__main__':
    socketio.run(app, debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true', host='0.0.0.0', port=int(os.getenv('PORT', 8000)))
from flask import Flask
from flask_socketio import SocketIO, emit  # New: SocketIO
from app.routers import email_router
from flask_cors import CORS
from app.services.gmail_service import enable_watch
import os

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # New: For SocketIO
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")  # New: SocketIO instance

app.register_blueprint(email_router.bp)

# Enable watch
enable_watch()

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=8000)  # Fixed: Use socketio.run
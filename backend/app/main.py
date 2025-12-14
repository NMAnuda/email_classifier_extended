from flask import Flask
from flask_socketio import SocketIO, emit
from flask_jwt_extended import JWTManager  # New: JWT auth
from app.routers import email_router
from flask_cors import CORS
from app.services.gmail_service import enable_watch
import os

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-change-in-prod')  # New: JWT key (env)

# CORS
cors_origins = os.getenv('FLASK_CORS_ORIGINS', 'http://localhost:3000')
CORS(app, origins=cors_origins)

# JWT
jwt = JWTManager(app)

socketio = SocketIO(app, cors_allowed_origins=cors_origins)
app.register_blueprint(email_router.bp)
enable_watch()

if __name__ == '__main__':
    socketio.run(app, debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true', host='0.0.0.0', port=int(os.getenv('PORT', 8000)), workers=1)
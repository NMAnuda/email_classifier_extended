from flask import Blueprint, request, jsonify
import os
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app.database.db import SessionLocal, User  # User model (add if missing)

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Your Gmail owner email (env var—only this user accesses)
OWNER_EMAIL = os.getenv('OWNER_EMAIL', 'your@gmail.com')  # Fixed: Match login to this

@bp.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if email != OWNER_EMAIL:  # Fixed: Only your email registers
        return jsonify({'error': 'Only owner email allowed'}), 403

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    hashed_pw = generate_password_hash(password)
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(email=email).first()
        if user:
            return jsonify({'error': 'User exists'}), 400

        new_user = User(email=email, password_hash=hashed_pw)
        session.add(new_user)
        session.commit()
        return jsonify({'message': 'Registered'}), 201
    finally:
        session.close()

@bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if email != OWNER_EMAIL:  # Fixed: Only your email logs in
        return jsonify({'error': 'Invalid credentials'}), 401

    session = SessionLocal()
    try:
        user = session.query(User).filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            access_token = create_access_token(identity=email)
            return jsonify({'access_token': access_token})
        return jsonify({'error': 'Invalid credentials'}), 401
    finally:
        session.close()
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app.database.db import SessionLocal, User  # Assume User model (add if missing)

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')

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

    session = SessionLocal()
    try:
        user = session.query(User).filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            access_token = create_access_token(identity=email)
            return jsonify({'access_token': access_token})
        return jsonify({'error': 'Invalid credentials'}), 401
    finally:
        session.close()

# Protect routes (add to email_router @bp.route)
# Example: @bp.route('/pull', methods=['GET'])
# @jwt_required()
# def pull_and_process():
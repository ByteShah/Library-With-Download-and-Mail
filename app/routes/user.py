from flask import request, jsonify
from app import db
from app.models import User, OTP
from datetime import datetime
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash

from . import user_bp

@user_bp.route('/register_user', methods=['POST'])
def register_user():
    data = request.json
    if not data or not data.get('email') or not data.get('name') or not data.get('phone_number') or not data.get('password'):
        return jsonify({"error": "Email, name, phone number, and password are required"}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already registered"}), 400

    otp_record = OTP.query.filter_by(email=data['email'], email_verified=True).first()
    if not otp_record:
        return jsonify({"error": "Email not verified"}), 400

    hashed_password = generate_password_hash(data['password'])

    new_user = User(
        name=data['name'],
        email=data['email'],
        phone_number=data['phone_number'],
        password_hash=hashed_password,
        created_at=datetime.utcnow()
    )
    db.session.add(new_user)
    db.session.commit()

    db.session.delete(otp_record)
    db.session.commit()

    access_token = create_access_token(identity=new_user.id)
    
    return jsonify({"message": "User registered successfully", "access_token": access_token, "user_id": new_user.id}), 201

@user_bp.route('/login_user', methods=['POST'])
def login_user():
    data = request.json
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=data['email']).first()
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({"error": "Invalid email or password"}), 401

    access_token = create_access_token(identity=user.id)
    
    return jsonify({"message": "Login successful", "access_token": access_token, "user_id": user.id}), 200

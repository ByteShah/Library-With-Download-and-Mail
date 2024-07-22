from flask import request, jsonify, render_template_string
from app import db, mail
from app.models import OTP
from flask_mail import Message
from datetime import datetime, timedelta
import random
import os

from . import auth_bp

def generate_otp():
    return str(random.randint(100000, 999999))

email_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OTP Verification</title>
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            font-family: 'Arial', sans-serif;
        }
        .email-container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        .email-header {
            text-align: center;
            padding: 20px 0;
            background-color: #405D72;
            color: #ffffff;
        }
        .email-header h1 {
            margin: 0;
            font-size: 24px;
            font-weight: bold;
        }
        .email-body {
            text-align: center;
            padding: 20px;
        }
        .email-body h2 {
            font-size: 20px;
            margin-bottom: 20px;
            color: #405D72;
        }
        .otp-block {
            display: inline-block;
            padding: 15px 30px;
            font-size: 28px;
            font-weight: bold;
            color: #FFF8F3;
            background-color: #405D72;
            border-radius: 5px;
            margin: 20px 0;
        }
        .email-body p {
            font-size: 16px;
            line-height: 1.5;
            color: #758694;
        }
        .email-footer {
            text-align: center;
            padding: 20px 0;
            font-size: 12px;
            color: #777777;
        }
        .email-footer p {
            margin: 0;
        }
        .btn {
            display: inline-block;
            padding: 10px 20px;
            font-size: 16px;
            color: #FFF8F3;
            background-color: #405D72;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="email-header">
            <h1>Librarify</h1>
        </div>
        <div class="email-body">
            <h2>Hey there!</h2>
            <p>Thanks for signing up for Librarify! We're excited to have you on board. To get started, please verify your email address by using the OTP below:</p>
            <div class="otp-block">{{ otp }}</div>
            <p>If you didn't request this email, no worries! Just ignore it and carry on.</p>
            <p>Cheers,<br>The Librarify Team</p>
            <a href="#" class="btn">Verify Now</a>
        </div>
        <div class="email-footer">
            <p>&copy; 2023 Librarify. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

@auth_bp.route('/send_otp', methods=['POST'])
def send_otp():
    data = request.json
    if not data or not data.get('email'):
        return jsonify({"error": "Email is required"}), 400

    email = data['email']
    otp = generate_otp()

    otp_record = OTP.query.filter_by(email=email).first()
    if otp_record:
        otp_record.otp = otp
        otp_record.created_at = datetime.utcnow()
    else:
        new_otp = OTP(email=email, otp=otp)
        db.session.add(new_otp)

    db.session.commit()

    sender_email = os.getenv('EMAIL_USER')
    sender_name = "Librarify"
    sender = f"{sender_name} <{sender_email}>"

    msg = Message("Your OTP Code", sender=sender, recipients=[email])
    msg.html = render_template_string(email_template, otp=otp)
    mail.send(msg)
    
    return jsonify({"message": "OTP sent to email"}), 200

@auth_bp.route('/verify_otp', methods=['POST'])
def verify_otp():
    data = request.json
    if not data or not data.get('email') or not data.get('otp'):
        return jsonify({"error": "Email and OTP are required"}), 400

    email = data['email']
    otp = data['otp']
    
    otp_record = OTP.query.filter_by(email=email, otp=otp).first()
    if not otp_record:
        return jsonify({"error": "Invalid OTP"}), 400

    if datetime.utcnow() > otp_record.created_at + timedelta(minutes=10):
        db.session.delete(otp_record)
        db.session.commit()
        return jsonify({"error": "OTP expired"}), 400
    
    otp_record.email_verified = True
    db.session.commit()
    
    return jsonify({"message": "OTP verified"}), 200
